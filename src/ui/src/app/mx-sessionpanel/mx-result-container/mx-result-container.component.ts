import { Component,
         ComponentFactory,
         ComponentFactoryResolver,
        //  ComponentResolver,
         Input,
         OnInit,
         ViewChild,
         ViewContainerRef } from '@angular/core';

import { MxResultPanelComponent } from './mx-result-panel';
import { MxResultslistPanelComponent } from './mx-resultslist-panel';

// Import agent components here
import * as mx from '../../agent_components/mx';
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

  current_result: string = 'none';
  current_displayed_component: string = 'empty';

  @Input() session_id: string;
  @Input() result_type: string;

  @ViewChild('target', { read: ViewContainerRef }) target;

  constructor(/* private compiler: ComponentResolver, */
              private componentfactoryResolver: ComponentFactoryResolver) { }

  ngOnInit() {}

  // A result has been selected - implement the agent interface
  selectResult(event) {

    // console.log('selectResult', event);

    // Save the current displayed result
    this.current_result = event.value;

    // Create a componentfactoryResolver instance
    const factory = this.componentfactoryResolver.resolveComponentFactory(mx_components['indexstrategyaaaa1component']);

    // Create the component
    let component = this.target.createComponent(factory);

    // Set the component current_result value
    component.instance.current_result = event.value;
  }

}
