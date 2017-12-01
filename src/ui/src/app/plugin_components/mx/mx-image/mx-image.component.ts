import { Component,
         Input,
         OnInit,
         ViewChild } from '@angular/core';
import { RestService } from '../../../shared/services/rest.service';


@Component({
  selector: 'app-mx-image',
  templateUrl: './mx-image.component.html',
  styleUrls: ['./mx-image.component.css']
})
export class MxImageComponent implements OnInit {

  @ViewChild('myCanvas') canvasRef: ElementRef;

  @Input()
  result: any = {};

  image_ctx: any;

  constructor(private rest_service: RestService) { }

  ngOnInit() {
    console.log('requesting image jpeg');

    let self = this;

    // let ctx: CanvasRenderingContext2D =
    // this.canvasRef.nativeElement.getContext('2d');

    // Draw the clip path that will mask everything else
    // that we'll draw later.
    // ctx.beginPath();
    // ctx.moveTo(250, 60);
    // ctx.lineTo(63.8, 126.4);
    // ctx.lineTo(92.2, 372.6);
    // ctx.lineTo(250, 460);
    // ctx.lineTo(407.8, 372.6);
    // ctx.lineTo(436.2, 126.4);
    // ctx.moveTo(250, 104.2);
    // ctx.lineTo(133.6, 365.2);
    // ctx.lineTo(177, 365.2);
    // ctx.lineTo(200.4, 306.8);
    // ctx.lineTo(299.2, 306.8);
    // ctx.lineTo(325.2, 365.2);
    // ctx.lineTo(362.6, 365.2);
    // ctx.lineTo(250, 104.2);
    // ctx.moveTo(304, 270.8);
    // ctx.lineTo(216, 270.8);
    // ctx.lineTo(250, 189);
    // ctx.lineTo(284, 270.8);
    // ctx.clip('evenodd');
    //
    // // Draw 50,000 circles at random points
    // ctx.beginPath();
    // ctx.fillStyle = '#DD0031';
    // for (let i=0 ; i < 50000 ; i++) {
    //   let x = Math.random() * 500;
    //   let y = Math.random() * 500;
    //   ctx.moveTo(x, y);
    //   ctx.arc(x, y, 1, 0, Math.PI * 2);
    // }
    // ctx.fill();

    this.rest_service.getImageJpeg({_id:this.result.image1._id})
          .subscribe(
            result => {
              console.log(result);
              // Put the response into an arraybuffer
				      // var arrayBufferView = new Uint8Array(result._body);
              // console.log(arrayBufferView);
				      // Create a blob with the arraybuffer
				      // var blob = new Blob([result._body ], {type: 'image/jpeg'});
              // console.log(blob);
              // Create a blob url
				      // var blob_url = window.URL.createObjectURL(blob);
              // console.log(blob_url);1
              // Load Image object with image
              var img = new Image();   // Create new img element
              img.addEventListener('load', function() {
                // execute drawImage statements here
                let ctx: CanvasRenderingContext2D = self.canvasRef.nativeElement.getContext('2d');
                // Clear and draw image
          			ctx.clearRect(0, 0, 1000, 1000);
          			ctx.drawImage(this, 0, 0, 1000, 1000);
                // Release the object URL
                // window.URL.revokeObjectURL(blob_url);
              }, false);
              img.src = 'data:image/jpeg;base64,'+result.image_data; // Set source path
            },
            error => {
              console.error(error);
            }
          );
  }

}
