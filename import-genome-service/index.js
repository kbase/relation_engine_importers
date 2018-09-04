const createRouter = require('@arangodb/foxx/router')
const joi = require('joi')
const db = require('@arangodb').db
const errors = require('@arangodb').errors

const DOC_NOT_FOUND = errors.ERROR_ARANGO_DOCUMENT_NOT_FOUND.code

const router = createRouter()

module.context.use(router)

const collections = {
  taxon: db._collection('taxon')
}

router.post('/taxon', function (req, res) {
  const data = req.body
  const meta = collections.taxon.save(req.body)
  res.send(Object.assign(data, meta))
})
  .body(joi.object().required(), 'New taxon entry.')
  .response(joi.object().required(), 'Stored data.')
  .summary('Store a new taxon document.')
  .description('Store a new entry in the "taxon" collection.')

router.get('/taxon/:key', function (req, res) {
  try {
    const data = collections.taxon.document(req.pathParams.key)
    res.send(data)
  } catch (e) {
    if (!e.isArangoError || e.errorNum !== DOC_NOT_FOUND) {
      throw e // Unexpected error
    } else {
      res.throw(404, 'Taxon not found', e)
    }
  }
})
  .pathParam('key', joi.string().required(), 'Key of the entry.')
  .response(joi.object().required(), 'Document data fo the found taxon.')
  .summary('Retrieve an entry.')
  .description('Retrieves an entry from the "taxon" collection by key.')
