import { Component,
         Input,
         OnInit } from '@angular/core';

@Component({
  selector: 'app-analysis-f068-2-0-0',
  templateUrl: './analysis-f068-2-0-0.component.html',
  styleUrls: ['./analysis-f068-2-0-0.component.css']
})
export class AnalysisF068200Component implements OnInit {

  @Input() result: any;
  objectKeys = Object.keys;
  
  constructor() { }

  ngOnInit() {

    console.log(this.result);

  }

}