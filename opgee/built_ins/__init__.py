from .compare_plugin import CompareCommand
from .config_plugin import ConfigCommand
from .graph_plugin import GraphCommand
from .run_plugin import RunCommand
from .csv2xml_plugin import Csv2XmlCommand
from .merge_plugin import MergeCommand
from .update_plugin import UpdateCommand

BuiltinSubcommands = [
    CompareCommand,
    ConfigCommand,
    Csv2XmlCommand,
    GraphCommand,
    MergeCommand,
    RunCommand,
    UpdateCommand,
]
