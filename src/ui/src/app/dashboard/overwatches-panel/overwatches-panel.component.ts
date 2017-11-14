import { Component,
         OnInit } from '@angular/core';

import { RestService } from '../../shared/services/rest.service';
import { User } from '../../shared/classes/user';

@Component({
  selector: 'app-overwatches-panel',
  templateUrl: './overwatches-panel.component.html',
  styleUrls: ['./overwatches-panel.component.css']
})
export class OverwatchesPanelComponent implements OnInit {

  private error_message:string;
  private overwatches: any[];
  public user: User;

  constructor(private rest_service: RestService) { }

  ngOnInit() {

    // Get the user profile
    this.user = JSON.parse(localStorage.getItem('profile'));

    this.getOverwatches();
  }

  getOverwatches() {
    this.rest_service.getOverwatches()
      .subscribe(
       overwatches => {
         this.overwatches = overwatches;
         console.log(overwatches);
       },
       error => this.error_message = <any>error);
  }

}
