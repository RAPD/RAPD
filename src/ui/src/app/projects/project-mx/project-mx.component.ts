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
import { MrDialogComponent } from '../../plugin_components/mx/mr-dialog/mr-dialog.component';
import { MergeDialogComponent } from '../../plugin_components/mx/merge-dialog/merge-dialog.component';
import { SadDialogComponent } from '../../plugin_components/mx/sad-dialog/sad-dialog.component';

import { Project } from "../../shared/classes/project";

import { ConfirmDialogComponent } from "../../shared/dialogs/confirm-dialog/confirm-dialog.component";
import { ErrorDialogComponent } from "../../shared/dialogs/error-dialog/error-dialog.component";

import { GlobalsService } from "../../shared/services/globals.service";
import { RestService } from "../../shared/services/rest.service";
import { WebsocketService } from "../../shared/services/websocket.service";

// Import agent components here
import * as mx from "../../plugin_components/mx";
// const MX_VALUES: any[] = [];
const MX_COMPONENTS: any = {};
for (const [key, value] of (<any>Object).entries(mx)) {
  // MX_VALUES.push(value);
  MX_COMPONENTS[key.toLowerCase()] = value;
}

@Component({
  selector: "app-project-mx",
  templateUrl: "./project-mx.component.html",
  styleUrls: ["./project-mx.component.css"]
})
export class ProjectMxComponent implements OnInit {

  public uploader: FileUploader;
  public project: Project;

  private id: string = '';
  private selectedIntegratedData: string[] = [];
  private selectedIntegrateAction: string = "";
  private actions: any = {
    INDEX: ["Display Result", "Remove"],
    INTEGRATE: [
      ["ReIntegrate", "MR", "SAD", "Display Result", "Remove"],
      ["Merge"],
    ],
  };

  public actionIcons: any = {
    "Display Result": "visibility",
    "MR": "search",
    "Merge": "call_merge",
    "ReIntegrate": "refresh",
    "Remove": "delete",
    "SAD": "search",
  };

  public selectedIndexedData: string[] = [];

  // Where results got
  @ViewChild("output_outlet", { read: ViewContainerRef }) outlet: any;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private globalsService: GlobalsService,
    private restService: RestService,
    private websocketService: WebsocketService,
    private componentfactoryResolver: ComponentFactoryResolver,
    public confirmDialog: MatDialog,
    public errorDialog: MatDialog,
    public reintegrateDialog: MatDialog,
    public mergeDialog: MatDialog,
    public mrDialog: MatDialog,
    public sadDialog: MatDialog
    // public upload_dialog: MatDialog,
  ) {}

  ngOnInit() {
    this.id = this.route.snapshot.paramMap.get('id');
    // console.log(this.id);
    this.getProject(this.id);

    this.uploader = new FileUploader({
      authToken: localStorage.getItem('access_token'),
      autoUpload: true,
      url: this.globalsService.site.restApiUrl + '/upload_mx_raw',
    });

    // Add form fields
    this.uploader.onBuildItemForm = (item, form) => {
      console.log("onBuildItemForm");
      console.log(item);
      console.log(form);
      form.append("foo", "bar");
    };

    // override the onAfterAddingfile property of the uploader so it doesn't authenticate with //credentials.
    this.uploader.onAfterAddingFile = (file) => {
      file.withCredentials = false;
    };

    this.uploader.onBeforeUploadItem = (item) => {
      console.log("onBeforeUploadItem");
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
    this.restService.getProject(id).subscribe(parameters => {
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

    const index = this.selectedIntegratedData.indexOf(id);
    // Add to selected data array
    if (index === -1) {
      this.selectedIntegratedData.push(id);
      this.selectedIndexedData = [];
      // Remove id from selected array
    } else {
      this.selectedIntegratedData.splice(index, 1);
    }
  }

  public toggleSourceDataIndexSelection(id: string) {
    const index = this.selectedIndexedData.indexOf(id);

    // Clear the result display?
    this.outlet.clear();

    // Add to selected data array
    if (index === -1) {
      this.selectedIndexedData.push(id);
      this.selectedIntegratedData = [];
      // Remove id from selected array
    } else {
      this.selectedIndexedData.splice(index, 1);
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
        this.displayResult(this.selectedIntegratedData[0]);
        break;

      case "ReIntegrate":
        this.activateReintegration(this.selectedIntegratedData[0]);
        break;

      case 'MR':
        this.activateMR(this.selectedIntegratedData[0]);
        break;

      case 'SAD':
        this.activateSAD(this.selectedIntegratedData[0]);
        break;

      case "Remove":
        this.activateRemoveConfirm(this.selectedIntegratedData[0]);
        break;

      default:
        break;
    }
  }

  public selectMultipleIntgrationAction(action: string) {

    console.log("selectMultipleIntgrationAction", action);

    switch (action) {
      case "Display Result":
        this.displayResult(this.selectedIntegratedData[0]);
        break;

      case "ReIntegrate":
        this.activateReintegration(this.selectedIntegratedData[0]);
        break;

      case "Remove":
        this.activateRemoveConfirm(this.selectedIntegratedData[0]);
        break;

      case 'Merge':
        console.log('Merge');
        this.activateMerge(this.selectedIntegratedData);
        break;

      default:
        break;
    }
  }

  public selectSingleIndexAction(action: string) {
    console.log("selectSingleIndexAction", action);

    switch (action) {
      case "Display Result":
        this.displayResult(this.selectedIndexedData[0]);
        break;

      case "Remove":
        this.activateRemoveConfirm(this.selectedIndexedData[0]);

      default:
        break;
    }
  }

  public displayResult(resultId: string) {

    console.log("displayResult", resultId);

    this.restService.getResult(resultId).subscribe(
      parameters => {
        console.log(parameters);
        if (parameters.success === true) {
          // For ease of use
          const result = parameters.result;
          // Work out the name of the component
          const componentName = (
            result.plugin_type +
            result.plugin_id +
            result.plugin_version.replace(/\./g, "") +
            "component"
          ).toLowerCase();
          console.log(componentName);
          // Create a componentfactoryResolver instance
          const factory = this.componentfactoryResolver.resolveComponentFactory(
            MX_COMPONENTS[componentName]
          );
          // Destroy the current component in the target view
          this.outlet.clear();
          // Create the component
          const component = this.outlet.createComponent(factory);
          // Set the component current_result value to the result
          component.instance.current_result = result;
        }
      }
      // error => this.error_message = <any>error)
    );
  }

  private activateReintegration(resultId: string) {
    console.log("activateReintegration", resultId);

    // Get the full result
    this.restService.getResultDetail(resultId).subscribe((parameters) => {
      console.log(parameters);
      if (parameters.success === true) {
        const dialogRef = this.reintegrateDialog.open(
          ReintegrateDialogComponent,
          {
            data: parameters.results,
          }
        );
      } else {
        const errorDialogRef = this.errorDialog.open(ErrorDialogComponent, {
          data: { message: parameters.message },
        });
      }
    });
  }

  private activateMR(resultId: string) {
    // Get the full result
    this.restService.getResultDetail(resultId).subscribe((parameters) => {
      console.log(parameters);
      parameters.results.current_project_id = this.id;
      if (parameters.success === true) {
        const dialogRef = this.mrDialog.open(MrDialogComponent, {data: parameters.results,});
      } else {
        const errorDialogRef = this.errorDialog.open(ErrorDialogComponent, {
          data: { message: parameters.message },
        });
      }
    });
  }

  private activateSAD(resultId: string) {
    // Get the full result
    this.restService.getResultDetail(resultId).subscribe((parameters) => {
      // console.log(parameters);
      parameters.results.current_project_id = this.id;
      if (parameters.success === true) {
        const dialogRef = this.sadDialog.open(SadDialogComponent, {data: parameters.results,});
      } else {
        const errorDialogRef = this.errorDialog.open(ErrorDialogComponent, {
          data: { message: parameters.message },
        });
      }
    });
  }

  private activateMerge(resultIds: string[]) {
    // Get the full result
    this.restService.getMultipleResultDetails(resultIds).subscribe((parameters) => {
      console.log(parameters);
      parameters.results.current_project_id = this.id;
      if (parameters.success === true) {
        const dialogRef = this.mergeDialog.open(MergeDialogComponent, {data: parameters.results, disableClose:true});
      } else {
        const errorDialogRef = this.errorDialog.open(ErrorDialogComponent, {
          data: { message: parameters.message },
        });
      }
    });
  }

  private activateMR(resultId: string) {
    // Get the full result
    this.rest_service.getResultDetail(resultId).subscribe((parameters) => {
      console.log(parameters);
      parameters.results.current_project_id = this.id;
      if (parameters.success === true) {
        const dialogRef = this.mrDialog.open(MrDialogComponent, {data: parameters.results,});
      } else {
        const errorDialogRef = this.error_dialog.open(ErrorDialogComponent, {
          data: { message: parameters.message },
        });
      }
    });
  }

  private activateSAD(resultId: string) {
    // Get the full result
    this.rest_service.getResultDetail(resultId).subscribe((parameters) => {
      // console.log(parameters);
      parameters.results.current_project_id = this.id;
      if (parameters.success === true) {
        const dialogRef = this.mrDialog.open(SadDialogComponent, {data: parameters.results,});
      } else {
        const errorDialogRef = this.error_dialog.open(ErrorDialogComponent, {
          data: { message: parameters.message },
        });
      }
    });
  }

  private activateMerge(resultIds: string[]) {
    // Get the full result
    this.rest_service.getMultipleResultDetails(resultIds).subscribe((parameters) => {
      console.log(parameters);
      parameters.results.current_project_id = this.id;
      if (parameters.success === true) {
        const dialogRef = this.mrDialog.open(MergeDialogComponent, {data: parameters.results, disableClose:true});
      } else {
        const errorDialogRef = this.error_dialog.open(ErrorDialogComponent, {
          data: { message: parameters.message },
        });
      }
    });
  }

  private activateRemoveConfirm(result_id: string) {
    console.log("activateRemoveConfirm", result_id);

    const label = this.project.source_data.filter((obj) => {
      return obj._id === result_id;
    })[0].repr;

    let dialogRef = this.confirmDialog.open(ConfirmDialogComponent, {
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
        const indexToRemove = this.project.source_data.findIndex((element) => {
          return element._id === result_id;
        });
        this.project.source_data.splice(indexToRemove, 1);

        // Remove from selectedIntegratedData
        const sidIndexToRemove = this.selectedIntegratedData.findIndex((element) => {
            return element === result_id;
          }
        );
        if (sidIndexToRemove !== -1) {
          this.selectedIntegratedData.splice(sidIndexToRemove, 1);
          // Clear the result display?
          this.outlet.clear();
        }

        // Remove from selectedIndexedData
        const sid2IndexToRemove = this.selectedIndexedData.findIndex((element) => {
          return element === result_id;
        });
        if (sidIndexToRemove !== -1) {
          this.selectedIndexedData.splice(sidIndexToRemove, 1);
          // Clear the result display?
          this.outlet.clear();
        }

        // Update the database
        this.restService.submitProject(this.project).subscribe(params => {
          console.log(params);
          // A problem connecting to REST server
          // Submitted is over
          // this.submitted = false;
          // this.submit_error = params.error;
          if (params.success) {
            // this.dialogRef.close(params);
          } else {
            const errorDialogRef = this.errorDialog.open(ErrorDialogComponent, {
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
