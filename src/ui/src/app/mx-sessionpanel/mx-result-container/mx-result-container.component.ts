import { Component,
         ComponentFactoryResolver,
         Input,
         OnInit,
         ViewChild,
         ViewContainerRef } from '@angular/core';

import { MxResultPanelComponent } from './mx-result-panel';
import { MxResultslistPanelComponent } from './mx-resultslist-panel';

// Import agent components here
import * as mx from '../../plugin_components/mx';
var mx_values = [];
var mx_components = {};
for (let key in mx) {
  mx_values.push(mx[key]);
  mx_components[key.toLowerCase()] = mx[key];
}

@Component({
  selector: 'app-mx-result-container',
  templateUrl: './mx-result-container.component.html',
  styleUrls: ['./mx-result-container.component.css'],
  providers: [ MxResultslistPanelComponent,
               MxResultPanelComponent ],
  entryComponents: mx_values
})
export class MxResultContainerComponent implements OnInit {

  currentResult: any = 'none';
  current_displayed_component: string = 'empty';

  @Input() session_id: string;
  @Input() result_type: string;

  @ViewChild('target', { read: ViewContainerRef, static: true }) target;

  constructor(private componentfactoryResolver: ComponentFactoryResolver) { }

  ngOnInit() {}

  // A result has been selected - implement the agent interface
  selectResult(event) {
    console.log('selectResult', event);

    // Destroy the current component in the target view
    this.target.clear();

    // Save the current displayed result
    this.currentResult = event.value;

    // Construct the component name from the result
    const component_name = (this.currentResult.plugin_type + this.currentResult.plugin_id + this.currentResult.plugin_version.replace(/\./g, '') + 'component').toLowerCase();

    // Create a componentfactoryResolver instance
    const factory = this.componentfactoryResolver.resolveComponentFactory(mx_components[component_name]);

    // Create the component
    let component = this.target.createComponent(factory);

    // Set the component currentResult value
    component.instance.currentResult = event.value;
  }

}
