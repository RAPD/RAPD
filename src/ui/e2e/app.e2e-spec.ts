import { Rapd21UiPage } from './app.po';

describe('rapd21-ui App', function() {
  let page: Rapd21UiPage;

  beforeEach(() => {
    page = new Rapd21UiPage();
  });

  it('should display message saying app works', () => {
    page.navigateTo();
    expect(page.getParagraphText()).toEqual('app works!');
  });
});
