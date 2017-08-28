import { Injectable } from '@angular/core';

import { ReplaySubject } from 'rxjs/Rx';

@Injectable()
export class ResultsService {

  private ws: WebSocket;

  public results_subject: ReplaySubject<string>;
  public result_details_subject: ReplaySubject<string>;

  constructor() {
    // this.newResultsSubject();
  }

  newResultsSubject() {
    // Create a new one
    this.results_subject = new ReplaySubject<string>(100);
  }

  // Initialize
  initializeWebsocket() {

    let token = localStorage.getItem('id_token');
    let self = this;

    // No previous websocket
    // if (! this.ws) {
    this.ws = new WebSocket('ws://' + window.location.hostname + ':3000');

    this.ws.onopen = function(e: MessageEvent) {
      console.log('Websocket connected');

      // Connected - now ask for all available results
      // console.log('Sending token', token);
      self.ws.send(JSON.stringify({request_type: 'initialize',
                                   token: token}));
      console.log('Websocket sent');

      // What to do with the message
      self.ws.onmessage = function(error: MessageEvent) {
        console.log(error);
        self.handleWebsocketMessage(error.data);
      };
    };
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
