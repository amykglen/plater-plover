import time

import pytest
import requests
from typing import Dict, Union, List


ASPIRIN_CURIE = "PUBCHEM.COMPOUND:2244"
TICLOPIDINE_CURIE = "PUBCHEM.COMPOUND:5472"
ACETAMINOPHEN_CURIE = "PUBCHEM.COMPOUND:1983"
PROC_CURIE = "NCBIGene:5624"
DIETHYLSTILBESTROL_CURIE = "PUBCHEM.COMPOUND:448537"
METHYLPREDNISOLONE_CURIE = "PUBCHEM.COMPOUND:23663977"
RHOBTB2_CURIE = "NCBIGene:23221"
DIABETES_CURIE = "MONDO:0005015"
DIABETES_T1_CURIE = "MONDO:0005147"
DIABETES_T2_CURIE = "MONDO:0005148"
CAUSES_INCREASE_CURIE = "GO:0051901"
INCREASED_CURIE = "GO:0051882"
PARKINSONS_CURIE = "MONDO:0005180"
BIPOLAR_CURIE = "MONDO:0004985"


def _print_kg(kg: Dict[str, Dict[str, Dict[str, Dict[str, Union[List[str], str, None]]]]]):
    nodes_by_qg_id = kg["nodes"]
    edges_by_qg_id = kg["edges"]
    for qnode_key, node_ids in sorted(nodes_by_qg_id.items()):
        print(f"{qnode_key}: {node_ids}")
    for qedge_key, edge_ids in sorted(edges_by_qg_id.items()):
        print(f"{qedge_key}: {edge_ids}")


def _run_query(trapi_qg: Dict[str, Dict[str, Dict[str, Union[List[str], str, None]]]]):
    response = requests.post(f"{pytest.endpoint}/query",
                             json={"message": {"query_graph": trapi_qg}, "submitter": "amy-test"},
                             headers={'accept': 'application/json'})
    print(f"Got response in {response.elapsed.total_seconds()} seconds")
    if response.status_code == 200:
        json_response = response.json()
        return json_response
    else:
        print(f"Response status code was {response.status_code}. Response was: {response.text}")
        return dict()


def test_simple():
    # Simplest one-hop
    query = {
       "edges": {
          "e00": {
             "subject": "n00",
             "object": "n01",
             "predicates": ["biolink:interacts_with"]
          }
       },
       "nodes": {
          "n00": {
             "ids": [ASPIRIN_CURIE]
          },
          "n01": {
             "categories": ["biolink:Protein"]
          }
       }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_2():
    # Output qnode is lacking a category
    query = {
       "edges": {
          "e00": {
             "subject": "n00",
             "object": "n01",
             "predicates": ["biolink:related_to"]
          }
       },
       "nodes": {
          "n00": {
             "ids": [ASPIRIN_CURIE],
             "categories": ["biolink:ChemicalEntity"]
          },
          "n01": {
          }
       }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_3():
    # No predicate is specified
    query = {
       "edges": {
          "e00": {
             "subject": "n00",
             "object": "n01"
          }
       },
       "nodes": {
          "n00": {
             "ids": [ASPIRIN_CURIE],
             "categories": ["biolink:ChemicalEntity"]
          },
          "n01": {
              "categories": ["biolink:ChemicalEntity"]
          }
       }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_4():
    # Multiple output categories
    query = {
       "edges": {
          "e00": {
             "subject": "n00",
             "object": "n01"
          }
       },
       "nodes": {
          "n00": {
             "ids": [ASPIRIN_CURIE]
          },
          "n01": {
              "categories": ["biolink:Protein", "biolink:Procedure"]
          }
       }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_5():
    # Multiple predicates
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01",
                "predicates": ["biolink:physically_interacts_with", "biolink:related_to"]
            }
        },
        "nodes": {
            "n00": {
                "ids": [ASPIRIN_CURIE]
            },
            "n01": {
                "categories": ["biolink:Protein", "biolink:Gene"]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_6():
    # Curie-to-curie query
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01"
            }
        },
        "nodes": {
            "n00": {
                "ids": [ASPIRIN_CURIE]
            },
            "n01": {
                "ids": [TICLOPIDINE_CURIE, ACETAMINOPHEN_CURIE]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_7():
    # Multiple curie query
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01"
            }
        },
        "nodes": {
            "n00": {
                "ids": [ASPIRIN_CURIE, PROC_CURIE]
            },
            "n01": {
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_symmetric():
    ids = [ASPIRIN_CURIE, METHYLPREDNISOLONE_CURIE]
    # Test predicate symmetry is handled properly
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01",
                "predicates": ["biolink:interacts_with"]
            }
        },
        "nodes": {
            "n00": {
                "ids": ids
            },
            "n01": {
            }
        }
    }
    response_symmetric = _run_query(query)

    query = {
        "edges": {
            "e00": {
                "subject": "n01",
                "object": "n00",
                "predicates": ["biolink:interacts_with"]
            }
        },
        "nodes": {
            "n00": {
                "ids": ids
            },
            "n01": {
            }
        }
    }
    response_symmetric_reversed = _run_query(query)

    assert response_symmetric["message"]["results"]
    assert response_symmetric_reversed["message"]["results"]

    assert len(response_symmetric["message"]["results"]) == len(response_symmetric_reversed["message"]["results"])


def test_asymmetric():
    # Test treats only returns edges with direction matching QG
    ids = [ASPIRIN_CURIE, METHYLPREDNISOLONE_CURIE]
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01",
                "predicates": ["biolink:treats"]
            }
        },
        "nodes": {
            "n00": {
                "ids": ids
            },
            "n01": {
                "categories": ["biolink:Disease"]
            }
        }
    }
    response_asymmetric = _run_query(query)
    assert response_asymmetric["message"]["results"]

    # Test no edges are returned for backwards treats query
    query = {
        "edges": {
            "e00": {
                "subject": "n01",
                "object": "n00",
                "predicates": ["biolink:treats"]
            }
        },
        "nodes": {
            "n00": {
                "ids": ids
            },
            "n01": {
                "categories": ["biolink:Disease"]
            }
        }
    }
    response_asymmetric_reversed = _run_query(query)
    assert not response_asymmetric_reversed["message"]["results"]


def test_13():
    # TRAPI 1.1 property names
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01",
                "predicates": ["biolink:interacts_with"]
            }
        },
        "nodes": {
            "n00": {
                "ids": [RHOBTB2_CURIE]
            },
            "n01": {
                "categories": ["biolink:ChemicalEntity"]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_14():
    # Test subclass_of reasoning
    query_subclass = {
        "edges": {
        },
        "nodes": {
            "n00": {
                "ids": [DIABETES_CURIE]
            }
        }
    }
    response = _run_query(query_subclass)
    assert response["message"]["results"]
    # TODO: Check that multiple n00s were actually returned..


def test_16():
    # Test mixins in the QG
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01"
            }
        },
        "nodes": {
            "n00": {
                "ids": [ACETAMINOPHEN_CURIE]
            },
            "n01": {
                "categories": ["biolink:PhysicalEssence"]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_17():
    # Test canonical predicate handling
    query_non_canonical = {
        "edges": {
            "e00": {
                "subject": "n01",
                "object": "n00",
                "predicates": ["biolink:treated_by"]
            }
        },
        "nodes": {
            "n00": {
                "ids": [ACETAMINOPHEN_CURIE]
            },
            "n01": {
                "categories": ["biolink:Disease"]
            }
        }
    }
    response_non_canonical = _run_query(query_non_canonical)
    assert response_non_canonical["message"]["results"]

    query_canonical = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01",
                "predicates": ["biolink:treats"]
            }
        },
        "nodes": {
            "n00": {
                "ids": [ACETAMINOPHEN_CURIE]
            },
            "n01": {
                "categories": ["biolink:Disease"]
            }
        }
    }
    response_canonical = _run_query(query_canonical)
    assert response_canonical["message"]["results"]

    assert len(response_canonical["message"]["results"]) == len(response_non_canonical["message"]["results"])


def test_18():
    # Test hierarchical category reasoning
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01",
                "predicates": ["biolink:interacts_with"]
            }
        },
        "nodes": {
            "n00": {
                "ids": [ACETAMINOPHEN_CURIE]
            },
            "n01": {
                "categories": ["biolink:NamedThing"]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]
    # TODO: not actually checking what categories are present in results..


def test_19():
    # Test hierarchical predicate reasoning
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01",
                "predicates": ["biolink:related_to"]
            }
        },
        "nodes": {
            "n00": {
                "ids": [ACETAMINOPHEN_CURIE]
            },
            "n01": {
                "categories": ["biolink:Protein"]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]
    # TODO: not actually checking what predicates are present in results..


def test_20():
    # Test that the proper 'query_id' mapping (for TRAPI) is returned
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01"
            }
        },
        "nodes": {
            "n00": {
                "ids": [DIABETES_CURIE, DIABETES_T2_CURIE]
            },
            "n01": {
                "categories": ["biolink:ChemicalEntity"]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]
    # TODO: Not actually checking query_id contents..


def test_21():
    # Test qualifiers
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01",
                "predicates": ["biolink:interacts_with"],  # This is the wrong regular predicate, but it shouldn't matter
                "qualifier_constraints": [
                    {"qualifier_set": [
                        {"qualifier_type_id": "biolink:qualified_predicate",
                         "qualifier_value": "biolink:causes"},
                        {"qualifier_type_id": "biolink:object_direction_qualifier",
                         "qualifier_value": "increased"}
                    ]}
                ]
            }
        },
        "nodes": {
            "n00": {
                "ids": [CAUSES_INCREASE_CURIE]
            },
            "n01": {
                "categories": ["biolink:NamedThing"]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_22():
    # Test qualifiers
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01",
                "predicates": ["biolink:interacts_with"],  # This is the wrong regular predicate, but it shouldn't matter
                "qualifier_constraints": [
                    {"qualifier_set": [
                        {"qualifier_type_id": "biolink:qualified_predicate",
                         "qualifier_value": "biolink:causes"},
                        {"qualifier_type_id": "biolink:object_aspect_qualifier",
                         "qualifier_value": "activity_or_abundance"}
                    ]}
                ]
            }
        },
        "nodes": {
            "n00": {
                "ids": [CAUSES_INCREASE_CURIE]
            },
            "n01": {
                "categories": ["biolink:NamedThing"]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_23():
    # Test qualifiers
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01",
                "predicates": ["biolink:interacts_with"],  # This is the wrong regular predicate, but it shouldn't matter
                "qualifier_constraints": [
                    {"qualifier_set": [
                        {"qualifier_type_id": "biolink:qualified_predicate",
                         "qualifier_value": "biolink:causes"},
                        {"qualifier_type_id": "biolink:object_direction_qualifier",
                         "qualifier_value": "increased"}
                    ]}
                ]
            }
        },
        "nodes": {
            "n00": {
                "ids": [CAUSES_INCREASE_CURIE]
            },
            "n01": {
                "categories": ["biolink:NamedThing"]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_24():
    # Test qualifiers
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01",
                "predicates": ["biolink:interacts_with"],  # This is the wrong regular predicate, but it shouldn't matter
                "qualifier_constraints": [
                    {"qualifier_set": [
                        {"qualifier_type_id": "biolink:qualified_predicate",
                         "qualifier_value": "biolink:causes"}
                    ]}
                ]
            }
        },
        "nodes": {
            "n00": {
                "ids": [CAUSES_INCREASE_CURIE]
            },
            "n01": {
                "categories": ["biolink:NamedThing"]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_25():
    # Test qualifiers
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01",
                "predicates": ["biolink:interacts_with"],  # This is the wrong regular predicate
            }
        },
        "nodes": {
            "n00": {
                "ids": [CAUSES_INCREASE_CURIE]
            },
            "n01": {
                "categories": ["biolink:NamedThing"]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_26():
    # Test qualifiers
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01",
                "predicates": ["biolink:interacts_with"],  # This is the wrong regular predicate
                "qualifier_constraints": [
                    {"qualifier_set": [
                        {"qualifier_type_id": "biolink:object_direction_qualifier",
                         "qualifier_value": "increased"},
                        {"qualifier_type_id": "biolink:object_aspect_qualifier",
                         "qualifier_value": "activity_or_abundance"}
                    ]}
                ]
            }
        },
        "nodes": {
            "n00": {
                "ids": [CAUSES_INCREASE_CURIE]
            },
            "n01": {
                "categories": ["biolink:NamedThing"]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_27():
    # Test qualifiers
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01",
                "predicates": ["biolink:regulates"],  # This is the correct regular predicate
            }
        },
        "nodes": {
            "n00": {
                "ids": [CAUSES_INCREASE_CURIE]
            },
            "n01": {
                "categories": ["biolink:NamedThing"]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_28():
    # Test qualifiers
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01",
                "predicates": ["biolink:regulates"],  # This is the correct regular predicate
                "qualifier_constraints": [
                    {"qualifier_set": [
                        {"qualifier_type_id": "biolink:qualified_predicate",
                         "qualifier_value": "biolink:causes"},
                        {"qualifier_type_id": "biolink:object_direction_qualifier",
                         "qualifier_value": "increased"},
                        {"qualifier_type_id": "biolink:object_aspect_qualifier",
                         "qualifier_value": "activity_or_abundance"}
                    ]}
                ]
            }
        },
        "nodes": {
            "n00": {
                "ids": [CAUSES_INCREASE_CURIE]
            },
            "n01": {
                "categories": ["biolink:NamedThing"]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_29():
    # Test qualifiers
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01",
                "qualifier_constraints": [
                    {"qualifier_set": [
                        {"qualifier_type_id": "biolink:qualified_predicate",
                         "qualifier_value": "biolink:causes"},
                        {"qualifier_type_id": "biolink:object_direction_qualifier",
                         "qualifier_value": "increased"},
                        {"qualifier_type_id": "biolink:object_aspect_qualifier",
                         "qualifier_value": "activity_or_abundance"}
                    ]}
                ]
            }
        },
        "nodes": {
            "n00": {
                "ids": [CAUSES_INCREASE_CURIE]
            },
            "n01": {
                "categories": ["biolink:NamedThing"]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_30():
    # Test qualifiers
    query = {
        "edges": {
            "e00": {
                "subject": "n00",
                "object": "n01",
                "qualifier_constraints": [
                    {"qualifier_set": [
                        {"qualifier_type_id": "biolink:object_aspect_qualifier",
                         "qualifier_value": "activity_or_abundance"}
                    ]}
                ]
            }
        },
        "nodes": {
            "n00": {
                "ids": [CAUSES_INCREASE_CURIE]
            },
            "n01": {
                "categories": ["biolink:NamedThing"]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]


def test_31():
    # Test treats
    query = {
        "edges": {
            "e00": {
                "subject": "n01",
                "object": "n00",
                "predicates": ["biolink:treats"]
            }
        },
        "nodes": {
            "n00": {
                "ids": [BIPOLAR_CURIE]
            },
            "n01": {
                "categories": ["biolink:Drug"]
            }
        }
    }
    response = _run_query(query)
    assert response["message"]["results"]


if __name__ == "__main__":
    pytest.main(['-v', 'test.py'])