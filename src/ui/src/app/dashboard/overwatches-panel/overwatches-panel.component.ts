import { Component,
         OnDestroy,
         OnInit } from '@angular/core';
import { MatSnackBar } from '@angular/material';
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

  constructor(private rest_service: RestService,
              public snackBar: MatSnackBar) { }

  ngOnInit() {

    // Get the user profile
    this.user = JSON.parse(localStorage.getItem('profile'));

    this.getOverwatches();
  }

  getOverwatches() {
    // console.log('getOverwatches');

    let self = this;

    this.rest_service.getOverwatches()
      .subscribe(
       results => {
         if (results.success === true) {
           this.overwatches = results.overwatches;
           // console.log(results.overwatches);
         }
         this.update_timeout = setTimeout(function() {
           self.getOverwatches();
         }, 10000);
       },
       error => this.error_message = <any>error);
  }

  // Stop the overwatch's child process
  stopOverwatch(parent:any) {
    if (parent.status !== 'stopped') {
      this.rest_service.stopOverwatch(parent.id).subscribe(
       parameters => {
         console.log(parameters);
        // TODO
         //  if (parameters.success) {
        //    let snackBarRef = this.snackBar.open('Stop requested', 'Ok', {
        //      duration: 5000,
        //    });
        //    parent.status = 'stop requested';
        //  }
       },
       error => this.error_message = <any>error);
    } else {
      let snackBarRef = this.snackBar.open('Can\'t stop a stopped process', 'Ok', {
        duration: 5000,
      });
    }
  }

  // Start the overwatch's child process
  startOverwatch(parent:any) {
    if (parent.status !== 'running') {
      this.rest_service.startOverwatch(parent.id).subscribe(
       parameters => {
         console.log(parameters);
        // TODO
         //  if (parameters.success) {
        //    let snackBarRef = this.snackBar.open('Start requested', 'Ok', {
        //      duration: 5000,
        //    });
        //    parent.status = 'start requested';
        //  }
       },
       error => this.error_message = <any>error);
    } else {
      let snackBarRef = this.snackBar.open('Cannot start a running process', 'Ok', {
        duration: 5000,
      });
    }


  }

  // stop all the overwatches
  stopAll() {

    // console.log('stopAll');

    this.rest_service.stopAllOverwatches().subscribe(
     parameters => {
       console.log(parameters);
      // TODO
       //  if (parameters.success) {
      //    let snackBarRef = this.snackBar.open('Stop all requested', 'Ok', {
      //      duration: 5000,
      //    });
      //    parent.status = 'start requested';
      //  }
     },
     error => this.error_message = <any>error);
}

  ngOnDestroy() {
    // console.log("DESTROYED");
    clearTimeout(this.update_timeout);
  }

}
