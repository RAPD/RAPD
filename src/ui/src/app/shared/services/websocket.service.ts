import { Injectable } from '@angular/core';

import { ReplaySubject } from 'rxjs/Rx';

import { GlobalsService } from './globals.service';

@Injectable()
export class WebsocketService {

  private websocketUrl: string;
  private ws: WebSocket;

  public results_subject: ReplaySubject<string>;
  public result_details_subject: ReplaySubject<string>;

  private timed_out: boolean = false;
  private connecting: boolean = false;

  constructor(private globals_service: GlobalsService) {
    this.websocketUrl = this.globals_service.site.websocketUrl;
  }

  newResultsSubject() {
    // Create a new one
    this.results_subject = new ReplaySubject<string>(100);
  }

  // Initialize
  initializeWebsocket() {

    let token = localStorage.getItem('id_token');
    let self = this;

    // Track state
    this.connecting = true;

    // Connect the websocket
    this.ws = new WebSocket(this.websocketUrl);

    var connection_timeout = setTimeout(function () {
      self.timed_out = true;
      self.ws.close();
      self.timed_out = false;
    }, 2000);

    this.ws.onopen = function(e: MessageEvent) {

      console.log('Websocket onopen');

      // Track state
      self.connecting = false;

      // Clear the connection timeout
      clearTimeout(connection_timeout);

      // Connected - now ask for all available results
      self.ws.send(JSON.stringify({request_type: 'initialize',
                                   token: token}));
    };

    // What to do with the message
    this.ws.onmessage = function(message: MessageEvent) {
      self.handleWebsocketMessage(message.data);
    };

    this.ws.onerror = function(ev: MessageEvent) {
      console.error(ev);
    };

    this.ws.onclose = function(ev: CloseEvent) {

      console.log('Websocket connection closed');
      console.error(ev);

      // Clear the connection timeout
      clearTimeout(connection_timeout);

      // Delete the websocket
      self.ws = null;

      setTimeout(function () {
        self.reconnect();
      }, 2000);
    };
  }

  reconnect() {
    console.log("attempting reconnect");
    this.initializeWebsocket();
  }

  handleWebsocketMessage(message: string) {

    let data = JSON.parse(message);
    let self = this;

    console.log(data);

    switch (data.msg_type) {

      case 'results':
        // Send the data to the subscribers
        self.results_subject.next(data);
        break;

      case 'result_details':
        self.result_details_subject.next(data.results);
        break;

      default:
        break;
    }

  }

  // Guard against addressing the socket before it's ready
  waitForSocketConnection(callback) {

    let self = this;

    // Couch the callback in code making sure the connection has been made
    setTimeout(
      function () {
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
  setSession(session_id: string, session_type: string) {

    console.log('setSession', session_id);

    let self = this;

    // Create a new results_subject
    this.newResultsSubject();

    // Request the data, but protected for connection
    this.waitForSocketConnection(function() {
      // Set the session
      self.ws.send(JSON.stringify({
        request_type: 'set_session',
        session_id: session_id
      }));
    });

    // Request the data, but protected for connection
    this.waitForSocketConnection(function() {
      // Request all results
      self.ws.send(JSON.stringify({
        request_type: 'get_results',
        data_type: session_type + ':all',
        session_id: session_id
      }));
    });
  }

  // Change the display mode for a result
  updateResult(result:any) {

    console.log('setDisplayMode', result);

    // Request to update result
    this.ws.send(JSON.stringify({
      request_type: 'update_result',
      result: result
    }));
  }

  // Get all results for a session
  subscribeResults(session_id: string): ReplaySubject<string> {

    console.log('subscribeResults session_id:', session_id);

    // Return the observable
    return this.results_subject;

  }

  // Get details for a result
  subscribeResultDetails(result_type: string,
                         result_id: string): ReplaySubject<string> {
    console.log('subscribeResultDetails  result_type =', result_type, 'result_id =', result_id);

    let self = this;

    this.result_details_subject = new ReplaySubject<string>(1);

    // Ask for result details, but protected for connection
    this.waitForSocketConnection(function() {
      // Request all results
      self.ws.send(JSON.stringify({
        request_type: 'get_result_details',
        result_type: result_type,
        result_id: result_id
      }));
    });

    // Return the ReplaySubject
    return this.result_details_subject;
  }

}
