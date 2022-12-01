import { Component } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'rapd2-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent {
  title = 'rapd2';

  constructor(private router: Router) {}

  changeMode(event:any) {
    // console.log(event.value);
    this.router.navigate(['/' + event.value], { queryParams: {} });
  }
}
