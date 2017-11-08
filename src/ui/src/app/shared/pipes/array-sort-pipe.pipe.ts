import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'arraySortPipe'
})
export class ArraySortPipePipe implements PipeTransform {

  transform(value: any, args?: any): any {
    return null;
  }

}
