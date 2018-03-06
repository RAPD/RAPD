import { Component,
         ElementRef,
         Input,
         OnInit,
         ViewChild } from '@angular/core';
import { FormControl,
         FormGroup } from '@angular/forms';
import { RestService } from '../../../shared/services/rest.service';


@Component({
  selector: 'app-mx-image',
  templateUrl: './mx-image.component.html',
  styleUrls: ['./mx-image.component.css']
})
export class MxImageComponent implements OnInit {

  @ViewChild('layer1') image_canvas: ElementRef;
  @ViewChild('layer2') drawing_canvas: ElementRef;
  @Input() result: any = {};

  error_string: string;
  image_ctx: any;

  view_color: string;  // Gray, Heat, Rainbow

  constructor(private rest_service: RestService) { }

  ngOnInit() {
    this.view_color = localStorage.getItem('mx-image-view_color');
    // console.log('this.view_color', this.view_color);
    if (! this.view_color) {
      this.view_color = 'Gray';
    }
    // console.log('this.view_color', this.view_color);
    this.readImage();
  }

  // Testing
  doSomething(event:any) {
    // console.log('doSomething');
    // console.log(event);
    // console.log('this.view_color', this.view_color);
    localStorage.setItem('mx-image-view_color', this.view_color);
    this.readImage();
  }

  readImage() {

    let self = this;

    this.rest_service.getImageJpeg({
      _id:this.result.image1._id,
      view_color:this.view_color
    })
    .subscribe(
      result => {
        console.log(result);
        if (result.success == true) {
          // Load Image object with image
          var img = new Image();   // Create new img element
          img.addEventListener('load', function() {
            // execute drawImage statements here
            let ctx: CanvasRenderingContext2D = self.image_canvas.nativeElement.getContext('2d');
            // Determine image size
            var x_dim,
                y_dim;
            if (self.result.image1.size1 >= self.result.image1.size2) {
              x_dim = 800;
              y_dim = x_dim * (self.result.image1.size2 / self.result.image1.size1);
            } else {
              y_dim = 800;
              x_dim = x_dim * (self.result.image1.size1 / self.result.image1.size2);
            }

            // Clear and draw image
            ctx.clearRect(0, 0, 800, 800);
            ctx.drawImage(this, 0, 0, x_dim, y_dim);

            // Call for beam center
            self.drawBeamCenter();

          }, false);
          img.src = 'data:image/jpeg;base64,'+result.image_data;
        } else {
          self.error_string = result.message;
        }
      },
      error => {
        console.error(error);
      }
    );
  }

  drawBeamCenter() {

    let ctx: CanvasRenderingContext2D = this.drawing_canvas.nativeElement.getContext('2d');

    // Dimensions and ratio
    let x_dim,
        y_dim,
        ratio;
    if (this.result.image1.size1 >= this.result.image1.size2) {
      x_dim = 800;
      y_dim = x_dim * (this.result.image1.size2 / this.result.image1.size1);
    } else {
      y_dim = 800;
      x_dim = x_dim * (this.result.image1.size1 / this.result.image1.size2);
    }

    let center_pos_x =  (this.result.image1.x_beam/this.result.image1.pixel_size)*(x_dim/this.result.image1.size1)
    let center_pos_y =  (this.result.image1.y_beam/this.result.image1.pixel_size)*(y_dim/this.result.image1.size2);

    console.log(center_pos_x, center_pos_y);

    ctx.lineWidth = 2;
    ctx.strokeStyle = 'rgb(255, 0, 0)';
    ctx.beginPath();
    ctx.moveTo(center_pos_x-7, center_pos_y);
    ctx.lineTo(center_pos_x+7, center_pos_y);
    ctx.moveTo(center_pos_x, center_pos_y-7);
    ctx.lineTo(center_pos_x, center_pos_y+7);
    ctx.closePath();
    ctx.stroke();
  }
}
