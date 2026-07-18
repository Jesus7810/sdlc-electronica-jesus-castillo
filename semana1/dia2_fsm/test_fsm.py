from fsm_demo import TrafficLightFSM, TrafficLightState


def test_initial_state_is_red():
    semaforo = TrafficLightFSM()

    assert semaforo.state == TrafficLightState.RED


def test_red_to_green():
    semaforo = TrafficLightFSM()

    semaforo.transition()

    assert semaforo.state == TrafficLightState.GREEN


def test_full_cycle_returns_to_red():
    semaforo = TrafficLightFSM()

    for _ in range(3):
        semaforo.transition()

    assert semaforo.state == TrafficLightState.RED


def test_cycle_count():
    semaforo = TrafficLightFSM()

    for _ in range(3):
        semaforo.transition()

    assert semaforo._cycle_count == 3