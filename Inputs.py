import random

Costs = {
    # System Element Costs
    "procurement_cost_h": 200,
    "procurement_cost_l": 100,
    # Number of personnel for manufacturing
    "n_personnel_man_h" : 15,
    "n_personnel_man_l" : 1,
    # Dollars per hour for manufacturing personnel
    "cdot_man_personnel_h" : 30,
    "cdot_man_personnel_l" : 15,
    # Number of hour to manufacture
    "man_num_hours_h" : 30,
    "man_num_hours_l" : 3,
    # Manufacture Cost
    "man_cost_h" : 1000,
    "man_cost_l" : 100,
    # Test cost
    "t_setup_h": 1000,
    "t_setup_l": 200,
    "t_execution_h": 500,
    "t_execution_l": 50,
    "t_teardown_h": 300,
    "t_teardown_l": 30,
    "t_setup_environment_h": 200,
    "t_setup_environment_l": 20,
    "t_setup_article_h": 200,
    "t_setup_article_l": 20,
    # Hours per Test operation
    "test_num_hours_h": 15,
    "test_num_hours_l": 1,
    # Number of personnel
    "n_personnel_setup_h": 10,
    "n_personnel_setup_l": 1,
    "n_personnel_teardown_h": 10,
    "n_personnel_teardown_l": 1,
    # Dollars per hour for personnel
    "cdot_setup_personnel_h": 30,
    "cdot_setup_personnel_l": 15,
    "cdot_teardown_personnel_h": 30,
    "cdot_teardown_personnel_l": 15,
    "cdot_environment_h": 30,
    "cdot_environment_l": 15,
    # Number of different Test Articles
    "test_article" : 10,
    # Number of different Environments
    "environment" : 10,
    # Number of different Instruments
    "instrument" : 10,
    # Number of different Teams
    "team" : 10,

}

class Analysis:
    def __init__(self):
        ...

class Inspection:
    def __init__(self):
        ...

class Demonstration:
    def __init__(self):
        ...

class Test:
    test_id = 0
    def __init__(self):
        self.test_id = self.set_test_id()
        # Test article number
        self.test_article = f"A-{
            random.randint(
            1,
            Costs["test_article"])
        }"
        # Environment number
        self.environment = f"E-{
            random.randint(
            1,
            Costs["environment"])
        }"
        # Instrument number
        self.instrument = f"I-{
            random.randint(
            1,
            Costs["instrument"])
        }"
        # Team number
        self.team = f"T-{
            random.randint(
            1,
            Costs["team"])
            }"
        # Costs for operation
        self.t_setup = random.randint(
            Costs["t_setup_l"],
            Costs["t_setup_h"]
        )
        self.t_execute = random.randint(
            Costs["t_execution_l"],
            Costs["t_execution_h"]
        )
        self.t_teardown = random.randint(
            Costs["t_teardown_l"],
            Costs["t_teardown_h"]
        )
        self.t_setup_environment = random.randint(
            Costs["t_setup_environment_l"],
            Costs["t_setup_environment_h"]
        )
        self.t_setup_article = random.randint(
            Costs["t_setup_article_l"],
            Costs["t_setup_article_h"]
        )
        # Number of personnel
        self.n_personnel_setup = random.randint(
            Costs["n_personnel_setup_l"],
            Costs["n_personnel_setup_h"]
        )
        self.n_personnel_teardown = random.randint(
            Costs["n_personnel_teardown_l"],
            Costs["n_personnel_teardown_h"]
        )
        # Cost per hour of these personnel
        self.cdot_setup_personnel = random.randint(
            Costs["cdot_setup_personnel_l"],
            Costs["cdot_setup_personnel_h"]
        )
        self.cdot_teardown_personnel = random.randint(
            Costs["cdot_teardown_personnel_l"],
            Costs["cdot_teardown_personnel_h"]
        )
        self.cdot_environment = random.randint(
            Costs["cdot_environment_l"],
            Costs["cdot_environment_h"]
        )
        # Hours per Test operation
        self.cdot_environment = random.randint(
            Costs["test_num_hours_l"],
            Costs["test_num_hours_h"]
        )

    def set_test_id(self):
        Test.test_id += 1
        return Test.test_id

# Weights and verification types to be choosen from
ver_weights = [0,0,0,1]
ver_types = [Analysis, Inspection, Demonstration, Test]


class FoundationalCosts:
    def __init__(self, manufatured_flag):
        self.procurement_cost = random.randint(
            Costs["procurement_cost_l"],
            Costs["procurement_cost_h"]
        )
        self.n_personnel_man = 0
        self.cdot_man_personnel = 0
        self.man_num_hours = 0
        self.man_cost = 0
        if(manufatured_flag):
            # Number of personnel for manufacturing
            self.n_personnel_man = random.randint(
            Costs["n_personnel_man_l"],
            Costs["n_personnel_man_h"]
            )
            self.cdot_man_personnel = random.randint(
            Costs["cdot_man_personnel_l"],
            Costs["cdot_man_personnel_h"]
            )
            self.man_num_hours = random.randint(
            Costs["man_num_hours_l"],
            Costs["man_num_hours_h"]
            )
            self.man_cost = random.randint(
            Costs["man_cost_l"],
            Costs["man_cost_h"]
            )
