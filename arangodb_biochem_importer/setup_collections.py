

def setup_collections(db, vertices, edges):
    """
    Create all the given vertices and edges if they don't exist.
    """
    print('required vertexes: ' + ', '.join(vertices))
    for name in vertices:
        if db.hasCollection(name):
            print('  has "%s" vertex' % name)
        else:
            db.createCollection(name=name)
            print('  created %s vertex' % name)
    print('required edges: ' + ', '.join(edges))
    for name in edges:
        if db.hasCollection(name):
            print('  has "%s" edge' % name)
        else:
            db.createCollection(name=name, className='Edges')
            print('  created %s edge' % name)
    print('done setting up collections.')
