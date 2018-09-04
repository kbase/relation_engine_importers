const db = require('@arangodb').db

if (!db._collection('taxon')) {
  db._createDocumentCollection('taxon')
}

