import {
  Component,
  //  OnDestroy,
  OnInit,
  Input,
  Output,
  Pipe,
  PipeTransform,
  EventEmitter
} from "@angular/core";
import { ReplaySubject } from "rxjs/Rx";
import { Highlight } from "../../../shared/directives/highlight.directive";
import { WebsocketService } from "../../../shared/services/websocket.service";

@Component({
  selector: "app-mx-resultslist-panel",
  templateUrl: "./mx-resultslist-panel.component.html",
  styleUrls: ["./mx-resultslist-panel.component.css"]
})
export class MxResultslistPanelComponent implements OnInit /*, OnDestroy*/ {
  highlightColor = "white";
  message: string = "";

  // The currently active result
  activeResult: string = '';

  // Arrays for holding result thumbnail data structures
  dataResults: any[] = [];
  newResultTimeout: any;
  orphanChildren: any = {};

  // Object for holding progressbar counters
  // progressbar_counters: any = {};

  incomingData$: ReplaySubject<string>;

  resultTypes: any = {
    INDEX: "MX:INDEX",
    INTEGRATE: "MX:INTEGRATE",
    MERGE: "MX:MERGE",
    MR: "MX:MR",
    SAD: "MX:SAD",
    MAD: "MX:MAD",
  };

  @Input() sessionId: string = '';
  @Input() resultType: string = '';
  @Output() resultSelect = new EventEmitter();

  constructor(private websocketService: WebsocketService) {}

  ngOnInit() {
    this.incomingData$ = this.websocketService.subscribeResults(
      this.sessionId,
      this.resultType,
    );
    this.incomingData$.subscribe(x => this.handleIncomingData(x));
  }

  ngOnDestroy() {
    // this.websocket_service.unsubscribeResults(this.incomingData$);
    this.websocketService.unsubscribeResults();
  }

  private handleIncomingData(data: any) {

    const self = this;

    // console.log(data);

    for (const result of data) {
      // console.log(result);

      // My kind of data
      if ((result.data_type + ":" + result.plugin_type) === this.resultTypes[this.resultType]) {

        // console.log('Adding to', this.resultTypes[this.resultType], 'results');

        // Filter for age & status
        if (!result.display) {
          if (result.status > 0 && result.status < 99) {
            const resultTime: any = Date.parse(result.timestamp);
            if (Date.now() - resultTime > 3600000) {
              return false;
            }
          }
        }

        // Look for index of result
        let dataResultsIndex = this.dataResults.findIndex((elem) => {
          if (elem._id === result._id) {
            return true;
          } else {
            return false;
          }
        });
        // Update
        if (dataResultsIndex !== -1) {
          // console.log('  Updated data');
          this.dataResults[dataResultsIndex] = result;
          // Insert
        } else {
          // console.log('  New data');
          this.dataResults.unshift(result);
          dataResultsIndex = 0;
        }

        // Update parent objects
        if (result.parent_id) {
          // console.log('Have parent_id', result.parent_id);
          const parentResult = this.getResult(result.parent_id);
          if (parentResult) {
            // console.log('parentResult:', parentResult);
            // Look for index of result
            if (parentResult.children) {
              const myIndex = parentResult.children.findIndex((elem: any) => {
                if (elem._id === result._id) {
                  return true;
                } else {
                  return false;
                }
              });
              // Update
              // console.log('  myIndex:', myIndex);
              if (myIndex !== -1) {
                // console.log('  Updated data');
                parentResult.children[myIndex] = result;
                // Insert
              } else {
                // console.log('  New data');
                parentResult.children.unshift(result);
              }
            }
            // No parent result yet
          } else {
            // console.log('No parentResult yet');
            // Create entry for orphan child results
            if (!(result.parent_id in this.orphanChildren)) {
              this.orphanChildren[result.parent_id] = [];
            }
            // console.log('Add to orphanChildren');
            this.orphanChildren[result.parent_id].push(result);
          }

          // No parent - check for children
        } else {
          if (result._id in this.orphanChildren) {
            // console.log('Adding orphan children to parent');
            this.dataResults[
              dataResultsIndex
            ].children = this.orphanChildren[result._id];
            delete this.orphanChildren[result._id];
          } else {
            this.dataResults[dataResultsIndex].children = [];
          }
        }
      }
    }

    if (this.newResultTimeout) {
      clearTimeout(this.newResultTimeout);
    }
    this.newResultTimeout = setTimeout(() => {
      // Sort the data array
      self.dataResults.sort((a, b) => {
        if (a.timestamp > b.timestamp) {
          return -1;
        } else if (a.timestamp < b.timestamp) {
          return 1;
        } else {
          return 0;
        }
      });
    }, 200);
  }

  private getResult(id: string) {
    return this.dataResults.find((elem) => {
      if (elem._id === id) {
        return true;
      } else {
        return false;
      }
    });
  }

  public onClick(id: string) {
    console.log("onClick", id);

    // Save the current result as the active result
    this.activeResult = id;

    // Use the result to call for full results
    this.resultSelect.emit({
      value: this.getResult(id),
    });
  }
}
