import { Component,
         ComponentFactoryResolver,
         OnInit,  
         ViewChild,
         ViewContainerRef } from '@angular/core';
import { Router, ActivatedRoute, ParamMap } from '@angular/router';

import 'rxjs/add/operator/switchMap';
import { Observable } from 'rxjs/Observable';

import { Project } from '../../shared/classes/project';
import { RestService } from '../../shared/services/rest.service';
import { WebsocketService } from '../../shared/services/websocket.service';

// Import agent components here
import * as mx from '../../plugin_components/mx';
var mx_values = [];
var mx_components = {};
for (let key in mx) {
  mx_values.push(mx[key]);
  mx_components[key.toLowerCase()] = mx[key];
}

@Component({
  selector: 'app-project-mx',
  templateUrl: './project-mx.component.html',
  styleUrls: ['./project-mx.component.css']
})
export class ProjectMxComponent implements OnInit {

  id: string;
  project: Project;
  selected_integrated_data: string[]=[];
  selected_integrate_action: string="";
  actions: any = {
    'INTEGRATE': [['Display Result', 'ReIntegrate', 'MR', 'SAD', 'Remove'],['Merge', 'Remove']],
    'INDEX': ['Display Result', 'Remove']
  }
  action_icons: any = {
    'Display Result': 'visibility',
    'Merge': 'call_merge',
    'MR': 'search',
    'ReIntegrate': 'refresh',
    'Remove': 'delete',
    'SAD': 'search'
  }

  // Where results got
  @ViewChild('output_outlet', { read: ViewContainerRef }) outlet;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private rest_service: RestService,
    private websocket_service: WebsocketService,
    private componentfactoryResolver: ComponentFactoryResolver
  ) { }

  ngOnInit() {
    this.id = this.route.snapshot.paramMap.get('id');
    // console.log(this.id);
    this.getProject(this.id);
  }

  getProject(id:string) {
    this.rest_service.getProject(id)
      .subscribe(
        parameters => {
          console.log(parameters);
          if (parameters.success === true) {
            this.project = parameters.project;
          }
        }
      )
  }

  toggleSourceDataSelection(id:string) {
    console.log('toggleSourceDataSelection', id);

    let index = this.selected_integrated_data.indexOf(id);
    // Add to selected data array
    if (index === -1) {
      this.selected_integrated_data.push(id)
    // Remove id from selected array
    } else {
      this.selected_integrated_data.splice(index, 1);
    }
  }

  selectSingleIntgrationAction(action:string) {
    console.log('selectSingleIntgrationAction', action);

    switch (action) {
      case 'Display Result':
        this.displayResult(this.selected_integrated_data[0]);
        break;
    
      default:
        break;
    }
  }

  displayResult(result_id:string) {
    console.log('displayResult', result_id);

    this.rest_service.getResult(result_id).subscribe(
        parameters => {
          console.log(parameters);
          if (parameters.success === true) {
            // For ease of use
            const result = parameters.result;
            // Work out the name of the component
            const component_name = (result.plugin_type + result.plugin_id + result.plugin_version.replace(/\./g, '') + 'component').toLowerCase();
            console.log(component_name);
            // Create a componentfactoryResolver instance
            const factory = this.componentfactoryResolver.resolveComponentFactory(mx_components[component_name]);
            // Destroy the current component in the target view
            this.outlet.clear();
            // Create the component
            let component = this.outlet.createComponent(factory);
            // Set the component current_result value to the result
            component.instance.current_result = result;
          }
        },
        // error => this.error_message = <any>error)
    );
  }

  // A result has been selected - implement the agent interface
  selectResult(event) {

    console.log('selectResult', event);

    // Destroy the current component in the target view
    this.target.clear();

    // Save the current displayed result
    // this.current_result = event.value;

    // Construct the component name from the result
    // const component_name = (this.current_result.plugin_type + this.current_result.plugin_id + this.current_result.plugin_version.replace(/\./g, '') + 'component').toLowerCase();

    // console.log(component_name);
    // console.log(mx_components);

    // Create a componentfactoryResolver instance
    // const factory = this.componentfactoryResolver.resolveComponentFactory(mx_components[component_name]);

    // Create the component
    // let component = this.target.createComponent(factory);

    // Set the component current_result value
    // component.instance.current_result = event.value;
  }
}
