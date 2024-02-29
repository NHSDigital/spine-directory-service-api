device_schema = {
    "type": "object",
    "properties": {
        "resourceType": {"type": "string"},
        "id": {"type": "string"},
        "type": {"type": "string"},
        "total": {"type": "integer"},
        "link": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "relation": {"type": "string"},
                    "url": {"type": "string"}
                }
            }
        },
        "entry": {
            "type": "array",
            "items": {
                "resourceType": {"type": "string"},
                "id": {"type": "string"},
                "type": {"type": "string"},
                "total": {"type": "integer"},
                "link": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "relation": {"type": "string"},
                            "url": {"type": "string"}
                        }
                    }
                },
                "entry": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            {
                                "type": "object",
                                "properties": {
                                    "fullUrl": {"type": "string"},
                                    "resource": {
                                        "type": "object",
                                        "properties": {
                                            "resourceType": {"type": "string"},
                                            "deviceName": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "name": {"type": "string"},
                                                        "type": {"type": "string"}
                                                    }
                                                }
                                            },
                                            "definition": {
                                                "type": "object",
                                                "properties": {
                                                    "identifier": {
                                                        "type": "object",
                                                        "properties": {
                                                            "system": {"type": "string"},
                                                            "value": {"type": "string"}
                                                        }
                                                    }
                                                }
                                            },
                                            "identifier": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "system": {"type": "string"},
                                                        "value": {"type": "string"}
                                                    }
                                                }
                                            },
                                            "owner": {
                                                "type": "object",
                                                "properties": {
                                                    "identifier": {
                                                        "type": "object",
                                                        "properties": {
                                                            "system": {"type": "string"},
                                                            "value": {"type": "string"}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "search": {
                                        "type": "object",
                                        "properties": {
                                            "mode": {"type": "string"}
                                        }
                                    }
                                }
                            },
                            {
                                {
                                    "type": "object",
                                    "properties": {
                                        "resourceType": {"type": "string"},
                                        "identifier": {"type": "string"},
                                        "questionnaire": {"type": "string"},
                                        "status": {"type": "string"},
                                        "subject": {
                                            "type": "object",
                                            "properties": {
                                                "reference": {"type": "string"}
                                            }
                                        },
                                        "authored": {"type": "string"},
                                        "author": {
                                            "type": "object",
                                            "properties": {
                                                "reference": {"type": "string"}
                                            }
                                        },
                                        "item": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "link_id": {"type": "string"},
                                                    "text": {"type": "string"},
                                                    "answer": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "object",
                                                            "properties": {
                                                                "valueString": {"type": "string"},
                                                                "valueDateTime": {"type": "string"},
                                                                "valueInteger": {"type": "integer"}
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
