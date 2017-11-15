import { Component,
         OnDestroy,
         OnInit } from '@angular/core';

import { RestService } from '../../shared/services/rest.service';
import { User } from '../../shared/classes/user';

@Component({
  selector: 'app-overwatches-panel',
  templateUrl: './overwatches-panel.component.html',
  styleUrls: ['./overwatches-panel.component.css']
})
export class OverwatchesPanelComponent implements OnInit, OnDestroy {

  private error_message:string;
  private overwatches: any[];
  public user: User;

  private update_timeout:number;

  constructor(private rest_service: RestService) { }

  ngOnInit() {

    // Get the user profile
    this.user = JSON.parse(localStorage.getItem('profile'));

    this.getOverwatches();
  }

  getOverwatches() {
    console.log('getOverwatches');

    let self = this;

    this.rest_service.getOverwatches()
      .subscribe(
       overwatches => {
         this.overwatches = overwatches;
         console.log(overwatches);
         this.update_timeout = setTimeout(function() {
           self.getOverwatches();
         }, 10000);
       },
       error => this.error_message = <any>error);
  }

  // Stop the overwatch's child process
  stopOverwatch(id:string) {
    this.rest_service.stopOverwatch(id).subscribe(
     response => {
       console.log(response);
     },
     error => this.error_message = <any>error);
  }

  // Start the overwatch's child process
  startOverwatch(id:string) {
    this.rest_service.startOverwatch(id).subscribe(
     response => {
       console.log(response);
     },
     error => this.error_message = <any>error);
  }

  ngOnDestroy() {
    console.log("DESTROYED");
    clearTimeout(this.update_timeout);
  }

}
