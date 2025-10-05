
def test_mqtt_kafka_bridges_import():
    import importlib
    m1 = importlib.import_module('src.coach_feedback.asyncapi.mqtt_bridge')
    m2 = importlib.import_module('src.coach_feedback.asyncapi.kafka_bridge')
    assert hasattr(m1, 'start_bridge') and hasattr(m2, 'start_bridge')
