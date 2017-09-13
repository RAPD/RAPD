import { Component,
         Input,
         OnInit } from '@angular/core';

@Component({
  selector: 'app-log-card',
  templateUrl: './log-card.component.html',
  styleUrls: ['./log-card.component.css']
})
export class LogCardComponent implements OnInit {

  @Input()
  log: any = [];
  
  @Input()
  header: string = "";

  log_collapsed: boolean = true;

  constructor() { }

  ngOnInit() {

  }

}
