import { Injectable } from "@angular/core";

import { ReplaySubject } from "rxjs/Rx";

import { GlobalsService } from "./globals.service";

@Injectable()
export class WebsocketService {
  private websocketUrl: string;
  private ws: WebSocket;

  public results_subscribers = [];
  public details_subscribers = [];

  public results_subject: ReplaySubject<string>;
  public result_details_subject: ReplaySubject<string>;

  private timed_out: boolean = false;
  private connecting: boolean = false;

  constructor(private globalsService: GlobalsService) {
    this.websocketUrl = this.globalsService.site.websocketUrl;
  }

  newResultsSubject() {
    // Create a new one
    this.results_subject = new ReplaySubject<string>(100);
  }

  // Initialize
  initializeWebsocket() {
    let token = localStorage.getItem("access_token");
    let self = this;

    // Track state
    this.connecting = true;

    // Connect the websocket
    this.ws = new WebSocket(this.websocketUrl);

    var connection_timeout = setTimeout(function() {
      self.timed_out = true;
      self.ws.close();
      self.timed_out = false;
    }, 2000);

    this.ws.onopen = function(e: MessageEvent) {
      console.log("Websocket onopen");

      // Track state
      self.connecting = false;

      // Clear the connection timeout
      clearTimeout(connection_timeout);

      // Connected - now ask for all available results
      self.ws.send(
        JSON.stringify({
          request_type: "initialize",
          token: token
        })
      );
    };

    // What to do with the message
    this.ws.onmessage = function(message: MessageEvent) {
      console.log(message);
      self.handleWebsocketMessage(message.data);
    };

    this.ws.onerror = function(ev: MessageEvent) {
      console.error(ev);
    };

    this.ws.onclose = function(ev: CloseEvent) {
      console.log("Websocket connection closed");
      console.error(ev);

      // Clear the connection timeout
      clearTimeout(connection_timeout);

      // Delete the websocket
      self.ws = null;

      setTimeout(function() {
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
        data.results.forEach(function(result) {
          // console.log(result);
          // Send the data to the subscribers
          self.results_subscribers.forEach(function(subscriber) {
            if (subscriber.session_id === result.session_id) {
              subscriber.subject.next([result]);
            }
          });
        });
        break;

      // A detailed result
      case "result_details":
        if (data.results) {
          self.details_subscribers.forEach(function(subscriber) {
            if (subscriber._id == data.results.process.result_id) {
              subscriber.subject.next(data.results);
            }
          });
        }
        break;

      case "RAPD_RESULTS":
        // Send the data to the subscribers
        self.results_subject.next(data);
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

    // Share through globalsService
    this.globalsService.currentSession = sessionId;
    console.log(this.globalsService.currentSession);

    const self = this;

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
    this.waitForSocketConnection(function() {
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
    const self = this;

    // Store the observable
    this.results_subscribers.push({
      subject: resultsSubject,
      session_id,
    });

    // Return the observable
    return resultsSubject;
  }

  // Unsubscribe from result details
  unsubscribeResults() {
    console.log("unsubscribeResultDetails");

    console.log(this.results_subscribers);

    this.results_subscribers.forEach(function(subscriber) {
      subscriber["subject"].complete();
      subscriber = null;
    });

    // Empty the array
    this.results_subscribers = [];

    // Look through and remove
    // let index = this.results_subscribers.findIndex(function(element) {
    //   return element.subject === subject;
    // });
    // console.log(index);
    // if (index !== -1) {
    //   let subscriber = this.details_subscribers.splice(index, 1)[0];
    //   subscriber["subject"].complete();
    //   subscriber = null;
    // }
  }

  // Get details for a result
  subscribeResultDetails(
    dataType: string,
    pluginType: string,
    resultId: string,
    _id: string
  ): ReplaySubject<string> {
    // console.log(
    //   "subscribeResultDetails  data_type =",
    //   dataType,
    //   "plugin_type = ",
    //   pluginType,
    //   "result_id =",
    //   resultId,
    //   "_id =",
    //   _id
    // );

    const self = this;

    this.result_details_subject = new ReplaySubject<string>(1);

    const resultDetailsSubject = new ReplaySubject<string>(1);

    this.details_subscribers.push({
      subject: resultDetailsSubject,
      result_type: dataType + ":" + pluginType,
      data_type: dataType,
      plugin_type: pluginType,
      result_id: resultId,
      _id,
    });

    // Ask for result details, but protected for connection
    this.waitForSocketConnection(() => {
      // Request all results
      self.ws.send(
        JSON.stringify({
          request_type: "get_result_details",
          result_type: dataType + ":" + pluginType,
          data_type: dataType,
          plugin_type: pluginType,
          result_id: resultId,
          _id,
        })
      );
    });

    // Return the ReplaySubject
    return resultDetailsSubject;
  }

  // Unsubscribe from result details
  unsubscribeResultDetails(subject: ReplaySubject<string>) {
    console.log("unsubscribeResultDetails");

    let index = this.details_subscribers.findIndex(function(element) {
      return element.subject === subject;
    });
    let subscriber = this.details_subscribers.splice(index, 1)[0];
    subscriber["subject"].complete();
    subscriber = null;
  }
}
