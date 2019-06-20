import {
  Component,
  ComponentFactoryResolver,
  OnInit,
  ViewChild,
  ViewContainerRef
} from "@angular/core";

import { ActivatedRoute, ParamMap, Router } from "@angular/router";

import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from "@angular/material/dialog";
import { MatSnackBar } from "@angular/material/snack-bar";
import { MatToolbarModule } from "@angular/material/toolbar";

import "rxjs/add/operator/switchMap";
// import { Observable } from 'rxjs/Observable';

import { FileUploader } from "ng2-file-upload";

import { ReintegrateDialogComponent } from "../../plugin_components/mx/reintegrate-dialog/reintegrate-dialog.component";
// import { UploadDialogComponent } from '../../shared/dialogs/upload-dialog/upload-dialog.component';

import { Project } from "../../shared/classes/project";

import { ConfirmDialogComponent } from "../../shared/dialogs/confirm-dialog/confirm-dialog.component";
import { ErrorDialogComponent } from "../../shared/dialogs/error-dialog/error-dialog.component";

import { GlobalsService } from "../../shared/services/globals.service";
import { RestService } from "../../shared/services/rest.service";
import { WebsocketService } from "../../shared/services/websocket.service";

// Import agent components here
import * as mx from "../../plugin_components/mx";
var mx_values = [];
var mx_components = {};
for (let key in mx) {
  console.log(mx[key]);
  mx_values.push(mx[key]);
  mx_components[key.toLowerCase()] = mx[key];
}

@Component({
  selector: "app-project-mx",
  templateUrl: "./project-mx.component.html",
  styleUrls: ["./project-mx.component.css"]
})
export class ProjectMxComponent implements OnInit {
  public uploader: FileUploader;
  public project: Project;

  private id: string;
  private selected_integrated_data: string[] = [];
  private selected_integrate_action: string = "";
  private actions: any = {
    INDEX: ["Display Result", "Remove"],
    INTEGRATE: [
      ["ReIntegrate", "MR", "SAD", "Display Result", "Remove"],
      ["Merge"],
    ],
  };
  private actionIcons: any = {
    "Display Result": "visibility",
    "MR": "search",
    "Merge": "call_merge",
    "ReIntegrate": "refresh",
    "Remove": "delete",
    "SAD": "search",
  };

  private selected_indexed_data: string[] = [];

  // Where results got
  @ViewChild("output_outlet", { read: ViewContainerRef, static: false })
outlet;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private globals_service: GlobalsService,
    private rest_service: RestService,
    private websocket_service: WebsocketService,
    private componentfactoryResolver: ComponentFactoryResolver,
    public confirm_dialog: MatDialog,
    public error_dialog: MatDialog,
    public reintegrate_dialog: MatDialog // public upload_dialog: MatDialog
  ) {}

  ngOnInit() {
    this.id = this.route.snapshot.paramMap.get("id");
    // console.log(this.id);
    this.getProject(this.id);

    this.uploader = new FileUploader({
      url: this.globals_service.site.restApiUrl + "/upload_mx_raw",
      authToken: localStorage.getItem("access_token"),
      autoUpload: true
    });
    // override the onAfterAddingfile property of the uploader so it doesn't authenticate with //credentials.
    this.uploader.onAfterAddingFile = file => {
      file.withCredentials = false;
    };
    // overide the onCompleteItem property of the uploader so we are
    // able to deal with the server response.
    this.uploader.onCompleteItem = (
      item: any,
      response: any,
      status: any,
      headers: any
    ) => {
      console.log("ImageUpload:uploaded:", item, status, response);
    };
  }

  public getProject(id: string) {
    this.rest_service.getProject(id).subscribe(parameters => {
      console.log(parameters);
      if (parameters.success === true) {
        this.project = parameters.project;
      }
    });
  }

  public toggleSourceDataIntegrateSelection(id: string) {
    // console.log('toggleSourceDataSelection', id);

    // Clear the result display?
    this.outlet.clear();

    let index = this.selected_integrated_data.indexOf(id);
    // Add to selected data array
    if (index === -1) {
      this.selected_integrated_data.push(id);
      this.selected_indexed_data = [];
      // Remove id from selected array
    } else {
      this.selected_integrated_data.splice(index, 1);
    }
  }

  public toggleSourceDataIndexSelection(id: string) {
    let index = this.selected_indexed_data.indexOf(id);

    // Clear the result display?
    this.outlet.clear();

    // Add to selected data array
    if (index === -1) {
      this.selected_indexed_data.push(id);
      this.selected_integrated_data = [];
      // Remove id from selected array
    } else {
      this.selected_indexed_data.splice(index, 1);
    }
  }

  public toggleResultSelection(id:string) {

    console.log("toggleResultSelection", id);

    this.displayResult(id);
  }

  public selectSingleIntgrationAction(action: string) {
    console.log("selectSingleIntgrationAction", action);

    switch (action) {
      case "Display Result":
        this.displayResult(this.selected_integrated_data[0]);
        break;

      case "ReIntegrate":
        this.activateReintegration(this.selected_integrated_data[0]);
        break;

      case "Remove":
        this.activateRemoveConfirm(this.selected_integrated_data[0]);

      default:
        break;
    }
  }

  public selectMultipleIntgrationAction(action: string) {
    console.log("selectMultipleIntgrationAction", action);

    switch (action) {
      case "Display Result":
        this.displayResult(this.selected_integrated_data[0]);
        break;

      case "ReIntegrate":
        this.activateReintegration(this.selected_integrated_data[0]);
        break;

      case "Remove":
        this.activateRemoveConfirm(this.selected_integrated_data[0]);

      default:
        break;
    }
  }

  public selectSingleIndexAction(action: string) {
    console.log("selectSingleIndexAction", action);

    switch (action) {
      case "Display Result":
        this.displayResult(this.selected_indexed_data[0]);
        break;

      case "Remove":
        this.activateRemoveConfirm(this.selected_indexed_data[0]);

      default:
        break;
    }
  }

  public displayResult(resultId: string) {

    console.log("displayResult", resultId);

    this.rest_service.getResult(resultId).subscribe(
      parameters => {
        console.log(parameters);
        if (parameters.success === true) {
          // For ease of use
          const result = parameters.result;
          // Work out the name of the component
          const component_name = (
            result.plugin_type +
            result.plugin_id +
            result.plugin_version.replace(/\./g, "") +
            "component"
          ).toLowerCase();
          console.log(component_name);
          // Create a componentfactoryResolver instance
          const factory = this.componentfactoryResolver.resolveComponentFactory(
            mx_components[component_name]
          );
          // Destroy the current component in the target view
          this.outlet.clear();
          // Create the component
          let component = this.outlet.createComponent(factory);
          // Set the component current_result value to the result
          component.instance.current_result = result;
        }
      }
      // error => this.error_message = <any>error)
    );
  }

  private activateReintegration(result_id: string) {
    console.log("activateReintegration", result_id);

    // Get the full result
    this.rest_service.getResultDetail(result_id).subscribe((parameters) => {
      console.log(parameters);
      if (parameters.success === true) {
        let dialogRef = this.reintegrate_dialog.open(
          ReintegrateDialogComponent,
          {
            data: parameters.results,
          }
        );
      } else {
        let errorDialogRef = this.error_dialog.open(ErrorDialogComponent, {
          data: { message: parameters.message },
        });
      }
    });
  }

  private activateRemoveConfirm(result_id: string) {
    console.log("activateRemoveConfirm", result_id);

    let label = this.project.source_data.filter((obj) => {
      return obj._id === result_id;
    })[0].repr;

    let dialogRef = this.confirm_dialog.open(ConfirmDialogComponent, {
      data: {
        message:
          "Are you sure you want to remove " + label + " from the project?"
      }
    });

    dialogRef.afterClosed().subscribe(result => {
      // console.log('The dialog was closed', result);
      if (result == true) {
        // console.log('Removing from project');

        // Remove from project
        var index_to_remove = this.project.source_data.findIndex(function(
          element
        ) {
          return element._id === result_id;
        });
        this.project.source_data.splice(index_to_remove, 1);

        // Remove from selected_integrated_data
        var sid_index_to_remove = this.selected_integrated_data.findIndex(
          function(element) {
            return element === result_id;
          }
        );
        if (sid_index_to_remove !== -1) {
          this.selected_integrated_data.splice(sid_index_to_remove, 1);
          // Clear the result display?
          this.outlet.clear();
        }

        // Remove from selected_indexed_data
        var sid_index_to_remove = this.selected_indexed_data.findIndex(function(
          element
        ) {
          return element === result_id;
        });
        if (sid_index_to_remove !== -1) {
          this.selected_indexed_data.splice(sid_index_to_remove, 1);
          // Clear the result display?
          this.outlet.clear();
        }

        // Update the database
        this.rest_service.submitProject(this.project).subscribe(params => {
          console.log(params);
          // A problem connecting to REST server
          // Submitted is over
          // this.submitted = false;
          // this.submit_error = params.error;
          if (params.success) {
            // this.dialogRef.close(params);
          } else {
            let errorDialogRef = this.error_dialog.open(ErrorDialogComponent, {
              data: { message: params.message }
            });
          }
        });
      }
    });
  }

  // activateUpload() {

  //   console.log('activateUpload');

  //   // Open the dialog
  //   let uploadDialogRef = this.upload_dialog.open(UploadDialogComponent, {
  //     data: { upload_data_type: 'mx_data' }
  //   });
  // }

  handleFiles(files: any) {
    console.log(files);
  }
}
