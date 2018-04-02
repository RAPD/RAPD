import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';

import { AuthService } from '../services/auth.service';

@Injectable()
export class LoginGuard implements CanActivate {

  constructor(private auth_service: AuthService,
              private router: Router) {}

  public canActivate() {
      if (this.auth_service.authenticated()) {
        return true;
      } else {
        this.router.navigate(['unauthorized']);
        return false;
      }
  }
}
