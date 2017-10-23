import { Injectable } from '@angular/core';

import { ReplaySubject } from 'rxjs/Rx';

import { GlobalsService } from './globals.service';

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

      case 'result_details':
        //self.result_details_subject.next(data.results);
        console.log(data.results);
        if (data.results) {
          self.details_subscribers.forEach(function(subscriber) {
            if (subscriber.result_id == data.results._id) {
              subscriber.subject.next(data.results);
            }
          });
        }
        break;

      case 'RAPD_RESULTS':
        // Send the data to the subscribers
        self.results_subject.next(data);
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

    let results_subject = new ReplaySubject<string>(1);

    this.results_subscribers.push({
      subject:results_subject,
      session_id:session_id
    });

    // Return the observable
    return results_subject;

  }

  // Unsubscribe from result details
  unsubscribeResults(subject: ReplaySubject<string>) {
    console.log('unsubscribeResultDetails');

    let index = this.results_subscribers.findIndex(function(element){
      return element.subject === subject;
    });
    let subscriber = this.details_subscribers.splice(index, 1)[0];
    subscriber['subject'].complete();
    subscriber = null;
  }

  // Get details for a result
  subscribeResultDetails(data_type: string,
                         plugin_type: string,
                         result_id: string): ReplaySubject<string> {

    console.log('subscribeResultDetails  data_type =', data_type, 'plugin_type = ', plugin_type, 'result_id =', result_id);

    let self = this;

    this.result_details_subject = new ReplaySubject<string>(1);

    let result_details_subject = new ReplaySubject<string>(1);

    this.details_subscribers.push({
      subject:result_details_subject,
      result_type:data_type+':'+plugin_type,
      data_type:data_type,
      plugin_type:plugin_type,
      result_id:result_id
    });

    // Ask for result details, but protected for connection
    this.waitForSocketConnection(function() {
      // Request all results
      self.ws.send(JSON.stringify({
        request_type: 'get_result_details',
        result_type: data_type+':'+plugin_type,
        data_type:data_type,
        plugin_type:plugin_type,
        result_id: result_id
      }));
    });

    // Return the ReplaySubject
    return result_details_subject;
  }

  // Unsubscribe from result details
  unsubscribeResultDetails(subject: ReplaySubject<string>) {
    console.log('unsubscribeResultDetails');

    let index = this.details_subscribers.findIndex(function(element){
      return element.subject === subject;
    });
    let subscriber = this.details_subscribers.splice(index, 1)[0];
    subscriber['subject'].complete();
    subscriber = null;
  }

}
