from rdflib import Graph, Namespace, RDF, Literal, URIRef, XSD

def semanticise_data(data: dict, base_uri: str, ontology_uri: str) -> str:
    """
    Convert incoming JSON data into RDF Turtle.
    """
    g = Graph()
    MAIN = Namespace(ontology_uri)
    BASE = Namespace(base_uri)
    g.bind("sri4all", MAIN)
    g.bind("resource1", BASE)

    resource_uri = URIRef(base_uri + data["resource_id"])

    g.add((resource_uri, RDF.type, MAIN[data["type"]]))
    g.add((resource_uri, MAIN.hasValue, Literal(data["value"], datatype=XSD.float)))
    g.add((resource_uri, MAIN.hasUnit, Literal(data["unit"])))
    g.add((resource_uri, MAIN.hasTimestamp, Literal(data["timestamp"], datatype=XSD.dateTime)))

    return g.serialize(format="turtle")