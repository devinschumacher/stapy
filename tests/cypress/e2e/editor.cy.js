import data from '../fixtures/editor.json'

export class Action {
  static deletePage(pageData) {
    cy.visit(data.url.edit + pageData.path)
    cy.get('#i_title').invoke('val').then(($value) => {
      cy.get('[data-cy="delete"]').click()
      cy.on('window:confirm', () => true)
      if ($value) {
        cy.get('[data-cy="message-success"]')
          .should('be.visible')
          .contains(`Page "${pageData.path}" has been deleted`)
      } else {
        cy.get('[data-cy="message-error"]')
          .should('be.visible')
          .contains(`Page "${pageData.path}" does not exist`)
      }
    })
  }

  static addPage(pageData) {
    cy.visit(data.url.pages)
    cy.get('[data-cy="add"]').click()
    const fields = {
      "text": ["_full_path", "title"],
      "select": ["_page_type", "enabled", "tags"]
    }
    for (var i = 0; i < fields.text.length; i++) {
      cy.get('#i_' + fields.text[i]).type(pageData[fields.text[i]])
    }
    for (var j = 0; j < fields.select.length; j++) {
      cy.get('#i_' + fields.select[j]).select(pageData[fields.select[j]])
    }
    cy.get('.CodeMirror').click().type(pageData.content)
    cy.get('[data-cy="warning"]').contains('There are unsaved changes.');
    cy.get('[data-cy="save"]').click()
    cy.get('[data-cy="message-success"]').should('be.visible').contains('The page has been saved')
    cy.get('[data-cy="warning"]').should('be.empty');
  }

  static updatePage(pageData) {
    cy.intercept('POST', data.url.edit + pageData.path + '&ajax=1').as('ajax-save')
    cy.visit(data.url.edit + pageData.path)
    // Classic save when one or more fields are updated
    const fields = {
      'text': ['meta_title', 'meta_description'],
      'select': ['robots']
    }
    for (var i = 0; i < fields.text.length; i++) {
      cy.get('#i_' + fields.text[i]).type(pageData[fields.text[i]])
    }
    for (var j = 0; j < fields.select.length; j++) {
      cy.get('#i_' + fields.select[j]).select(pageData[fields.select[j]])
    }
    cy.get('[data-cy="warning"]').contains('There are unsaved changes.')
    cy.get('[data-cy="save"]').click()
    cy.get('[data-cy="message-success"]').should('be.visible').contains('The page has been saved')
    cy.get('[data-cy="warning"]').should('be.empty');

    // Save in Ajax when only the content has been updated
    cy.get('.CodeMirror').click().type(pageData.content)
    cy.get('[data-cy="warning"]').contains('There are unsaved changes.')
    cy.get('[data-cy="save"]').click()
    cy.wait('@ajax-save').its('response.statusCode').should('eq', 200)
    cy.get('[data-cy="message-success"]').should('be.visible').contains('The page has been saved')
    cy.get('[data-cy="warning"]').should('be.empty');
  }

  static viewPage(pageData) {
    cy.visit(data.url.edit + pageData.path)
    cy.get('[data-cy="view"]').invoke('removeAttr', 'target').click()
    cy.contains('Dès Noël où un zéphyr haï me vêt de glaçons würmiens je dîne d’exquis rôtis de bœuf au kir à l’aÿ d’âge mûr & cætera !')
  }

  static addMedia(filepath) {
    cy.visit(data.url.media)
    cy.get('[data-cy="file"]').selectFile(filepath)
    cy.get('[data-cy="save"]').click()
  }

  static copySnippet() {
    cy.visit(data.url.media)
    cy.get('[data-cy="media-html"]').first().click().then(($input) => {
      cy.window().then($win => {
        $win.navigator.clipboard.readText().then($text => {
          expect($text).to.eq($input.val())
        })
      })
    })
  }

  static deleteMedia() {
    cy.visit(data.url.media)
    cy.get('[data-cy="delete-file"]').first().then(($link) => {
      cy.visit($link.attr('href'))
      cy.on('window:confirm', () => true)
      cy.get('[data-cy="message-success"]')
          .should('be.visible')
          .contains(`File "${$link.attr('data-filename')}" has been deleted`)
    })
  }

  static createDirectory(name) {
    cy.visit(data.url.media)
    cy.get('[data-cy="folder"]').type(name)
    cy.get('[data-cy="save"]').click()
    cy.get('[data-cy="message-success"]').should('be.visible').contains('The folder has been created')
  }

  static openDirectory() {
    cy.visit(data.url.media)
    cy.get('[data-cy="folder-link"]').first().then(($link) => {
      cy.visit($link.attr('href'))
    });
  }

  static deleteDirectory() {
    cy.visit(data.url.media)
    cy.get('[data-cy="delete-folder"]').first().then(($link) => {
      cy.visit($link.attr('href'))
      cy.on('window:confirm', () => true)
      cy.get('[data-cy="message-success"]')
          .should('be.visible')
          .contains(`Folder "${$link.attr('data-filename')}" has been deleted`)
    })
  }
}

describe('Page tests', () => {
  it('Delete pages', () => {
    Action.deletePage(data.pages.js)
    Action.deletePage(data.pages.html)
    Action.deletePage(data.pages.md)
  })

  it('Add pages', () => {
    Action.addPage(data.pages.js)
    Action.addPage(data.pages.html)
    Action.addPage(data.pages.md)
  })

  it('View pages', () => {
    Action.viewPage(data.pages.html)
    cy.wait(1000)
    Action.viewPage(data.pages.md)
    cy.wait(1000)

    cy.visit(data.url.edit + data.pages.html.path)
    cy.get('[data-cy="view"]').invoke('removeAttr', 'target').click()
    cy.on('window:alert', (str) => {
      expect(str).to.equal('Hello World')
    })
  })

  it('Update pages', () => {
    Action.updatePage(data.pages.html)
    Action.updatePage(data.pages.md)
  })

  it('Delete pages', () => {
    Action.deletePage(data.pages.js)
    Action.deletePage(data.pages.html)
    Action.deletePage(data.pages.md)
  })
})

describe('Media tests', () => {
  it('Add Media', () => {
    Action.addMedia('cypress/media/picture.png')
    cy.get('[data-cy="message-success"]').should('be.visible').contains('The file has been uploaded')
    cy.wait(1000)
  })

  it('Copy HTML Snippet', () => {
    Action.copySnippet()
    cy.wait(1000)
  })

  it('Add not allowed Media', () => {
    Action.addMedia('cypress/media/data.json')
    cy.get('[data-cy="message-error"]').should('be.visible').contains('Media: "json" is not allowed')
    cy.wait(1000)
  })

  it('Delete Media', () => {
    Action.deleteMedia()
    cy.wait(1000)
  })

  it('Create directory', () => {
    Action.createDirectory('foobar')
    cy.wait(1000)
  })

  it('Open directory', () => {
    Action.openDirectory()
    cy.wait(1000)
  })

  it('Delete directory', () => {
    Action.deleteDirectory()
    cy.wait(1000)
  })
})
