import { Directive, ElementRef, Input } from '@angular/core';

@Directive({
  selector: '[myHighlight]',
  host: {
    '(mouseenter)': 'onMouseEnter()',
    '(mouseleave)': 'onMouseLeave()'
  }
})
export class Highlight {

  private _defaultColor = '#EEEEEE';
  private el: HTMLElement;

  @Input('myHighlight') highlightColor: string;

  constructor(el: ElementRef) {
    this.el = el.nativeElement;
  }

  onMouseEnter() { this.highlight(this.highlightColor || this._defaultColor); }

  onMouseLeave() {
    // if (this.clicked == false) {
      this.highlight(null);
    // }
  }

  private highlight(color: string) {
    this.el.style.backgroundColor = color;
  }
}
