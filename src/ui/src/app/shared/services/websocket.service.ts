import { Injectable, SkipSelf, ɵɵtrustConstantResourceUrl } from "@angular/core";
import { WebSocketSubject } from "rxjs/internal-compatibility";

import { ReplaySubject } from "rxjs/Rx";

import { GlobalsService } from "./globals.service";

@Injectable()
export class WebsocketService {
  private websocketUrl: string;
  private ws: WebSocket;

  public resultsSubscribers = [];
  public detailsSubscribers = [];

  public resultsSubject: ReplaySubject<string>;
  // public resultDetailsSubject: ReplaySubject<string>;

  private timedOut: boolean = false;
  private connecting: boolean = false;

  constructor(private globalsService: GlobalsService) {
    this.websocketUrl = this.globalsService.site.websocketUrl;
  }

  newResultsSubject() {
    // Create a new one
    this.resultsSubject = new ReplaySubject<string>(100);
  }

  // Initialize
  initializeWebsocket() {
    const token = localStorage.getItem("access_token");
    const self = this;

    // Track state
    this.connecting = true;

    // Connect the websocket
    this.ws = new WebSocket(this.websocketUrl);

    const connectionTimeout = setTimeout(() => {
      self.timedOut = true;
      self.ws.close();
      self.timedOut = false;
    }, 2000);

    this.ws.onopen = (e: MessageEvent) => {
      console.log("Websocket onopen");

      // Track state
      self.connecting = false;

      // Clear the connection timeout
      clearTimeout(connectionTimeout);

      // Connected - now ask for all available results
      self.ws.send(
        JSON.stringify({
          request_type: "initialize",
          token,
        })
      );

      //
      // This is a reconnection
      //
      if (this.globalsService.currentSessionId) {
        // console.log("Resending session data");
        this.setSession(this.globalsService.currentSessionId, this.globalsService.currentSessionType);
      }

      if (this.detailsSubscribers.length) {
        console.log("Will resubsscribe to", this.detailsSubscribers.length, "result details");
        this.detailsSubscribers.forEach((subject) => {
          self.requestResultDetails(subject);
        })
      }

    };

    // What to do with the message
    this.ws.onmessage = (message: MessageEvent) => {
      // console.log(message);
      self.handleWebsocketMessage(message.data);
    };

    this.ws.onerror = (ev: MessageEvent) => {
      console.error(ev);
    };

    this.ws.onclose = (ev: CloseEvent) => {
      console.log("Websocket connection closed");
      console.error(ev);

      // Clear the connection timeout
      clearTimeout(connectionTimeout);

      // Delete the websocket
      self.ws = null;

      setTimeout(() => {
        self.reconnect();
      }, 2000);
    };
  }

  reconnect() {
    console.log("attempting reconnect");
    this.initializeWebsocket();
  }

  handleWebsocketMessage(message: string) {
    // console.log(message);

    if (message === "ping") {
      return true;
    }

    let self = this;

    var data;
    if (typeof(message) === 'string') {
      data = JSON.parse(message);
    } else {
      data = message;
    }

    // console.log(data);

    switch (data.msg_type) {
      // A result has arrived
      case "results":
        console.log(data);
        data.results.forEach((result) => {
          // console.log(result);
          // Send the data to the subscribers
          self.resultsSubscribers.forEach((subscriber) => {
            if (subscriber.session_id === result.session_id) {
              subscriber.subject.next([result]);
            }
          });
        });
        break;

      // A detailed result
      case "result_details":
        if (data.results) {
          self.detailsSubscribers.forEach((subscriber) => {
            if (subscriber._id === data.results.process.result_id) {
              subscriber.subject.next(data.results);
            }
          });
        }
        break;

      case "RAPD_RESULTS":
        // Send the data to the subscribers
        self.resultsSubject.next(data);
        break;

      default:
        break;
    }

    return true;
  }

  // Guard against addressing the socket before it's ready
  waitForSocketConnection(callback) {
    let self = this;

    // Couch the callback in code making sure the connection has been made
    setTimeout(function() {
      if (self.ws.readyState === 1) {
        // console.log("Connection is made")
        callback();
        return;
      } else {
        // console.log("wait for connection...")
        self.waitForSocketConnection(callback);
      }
    }, 5);
  }

  // Inform the server what session this client is interested in
  setSession(sessionId: string, sessionType: string) {

    console.log("setSession", sessionId, sessionType);

    const self = this;

    // Share current session through globalsService
    this.globalsService.currentSessionId = sessionId;
    this.globalsService.currentSessionType = sessionType;

    // Create a new results_subject
    this.newResultsSubject();

    // Set session, but protected for connection
    this.waitForSocketConnection(() => {
      // Set the session
      self.ws.send(
        JSON.stringify({
          request_type: "set_session",
          session_id: sessionId,
        })
      );
    });

    // Request the data, but protected for connection
    this.waitForSocketConnection(() => {
      // Request all results
      self.ws.send(
        JSON.stringify({
          request_type: "get_results",
          data_type: sessionType + ":all",
          session_id: sessionId,
        })
      );
    });
  }

  // Inform the server that we are no longer interested in the session
  unsetSession() {

    console.log("unsetSession");

    const self = this;

    // Request the data, but protected for connection
    this.waitForSocketConnection(() => {
      // Set the session
      self.ws.send(
        JSON.stringify({
          request_type: "unset_session",
        })
      );
    });
  }

  // Change the display mode for a result
  updateResult(result: any) {
    // console.log('setDisplayMode', result);

    // Request to update result
    this.ws.send(
      JSON.stringify({
        request_type: "update_result",
        result: result
      })
    );
  }

  // Get all results for a session
  subscribeResults(session_id: string): ReplaySubject<string> {
    console.log("subscribeResults session_id:", session_id);

    const resultsSubject = new ReplaySubject<string>(1);

    // Store the observable
    this.resultsSubscribers.push({
      subject: resultsSubject,
      session_id,
    });

    // Return the observable
    return resultsSubject;
  }

  // Unsubscribe from all result details
  unsubscribeResults() {
    console.log("unsubscribeResultDetails");
    console.log(this.resultsSubscribers);

    this.resultsSubscribers.forEach((subscriber) => {
      subscriber.subject.complete();
      subscriber = null;
    });

    // Empty the array
    this.resultsSubscribers = [];
  }

  // Subscribe to and request details for a result
  subscribeResultDetails(
    dataType: string,
    pluginType: string,
    resultId: string,
    _id: string
  ): ReplaySubject<string> {

    const self = this;

    // Create ReplaySubject & preserve
    const resultDetailsSubject = new ReplaySubject<string>(1);
    this.detailsSubscribers.push({
      subject: resultDetailsSubject,
      result_type: (dataType + ":" + pluginType).toUpperCase(),
      data_type: dataType.toUpperCase(),
      plugin_type: pluginType.toUpperCase(),
      result_id: resultId,
      _id,
    });

    // Ask for result details, but protected for connection
    this.waitForSocketConnection(() => {
      // Request all results
      self.ws.send(
        JSON.stringify({
          request_type: "get_result_details",
          result_type: (dataType + ":" + pluginType).toUpperCase(),
          data_type: dataType.toUpperCase(),
          plugin_type: pluginType.toUpperCase(),
          result_id: resultId,
          _id,
        })
      );
    });

    // Return the ReplaySubject
    return resultDetailsSubject;
  }

  requestResultDetails(subject: any):void {
    const self = this;
    // Ask for result details, but protected for connection
    this.waitForSocketConnection(() => {
      // Request all results
      self.ws.send(
        JSON.stringify({
          request_type: "get_result_details",
          result_type: subject.result_type.toUpperCase(),
          data_type: subject.data_type.toUpperCase(),
          plugin_type: subject.plugin_type.toUpperCase(),
          result_id: subject.result_id,
          _id: subject._id,
        })
      );
    });
  }

  // Unsubscribe from result details
  unsubscribeResultDetails(subject: ReplaySubject<string>) {
    // console.log("unsubscribeResultDetails");
    const index = this.detailsSubscribers.findIndex((element) => {
      return element.subject === subject;
    });
    let subscriber = this.detailsSubscribers.splice(index, 1)[0];
    subscriber.subject.complete();
    subscriber = null;
  }
}
