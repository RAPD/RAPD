import { Component,
         OnInit } from '@angular/core';

import { RestService } from '../../shared/services/rest.service';
// import { Overwatcher } from '../../shared/classes/overwatcher';

@Component({
  selector: 'app-components-panel',
  templateUrl: './components-panel.component.html',
  styleUrls: ['./components-panel.component.css']
})
export class ComponentsPanelComponent implements OnInit {

  private error_message:string;
  components: any[];

  constructor(private rest_service: RestService) { }

  ngOnInit() {
    this.getComponents();
  }

  getComponents() {
    this.rest_service.getOverwatches()
      .subscribe(
       overwatches => {
         this.overwatches = overwatches;
         console.log(overwatches);
       },
       error => this.error_message = <any>error);
  }

}
