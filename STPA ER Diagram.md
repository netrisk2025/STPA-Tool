erDiagram
    System ||--o{ System            : has_child_system
    System ||--o{ Function          : Has
    System ||--o{ Interface         : Has
    System ||--o{ Asset             : Has
    System ||--o{ Constraint        : Has
    System ||--o{ Requirement       : Has
    System ||--o{ StateDiagram      : Has
    System ||--o{ ControlStructure  : Has
    System ||--o{ Environment       : Has

    Environment ||--o{ Hazard       : Creates
    Environment ||--o{ Interface    : May_Access

    Asset ||--o{ Loss               : has_loss
    Loss  ||--o{ SafetySecurityControl : mitigated_by

    Function ||--o{ ControlAlgorithm : Is
    Function ||--o{ ProcessModel      : Is

    Requirement ||--o{ SafetySecurityControl : Satisfies
    Constraint  ||--o{ Requirement          : is_a

    Hazard ||--o{ SafetySecurityControl : mitigated_by
    Hazard ||--o{ Asset                 : impairs

    ControlledProcess ||--o{ System    : Is_ControlledProcess
    ControlStructure  ||--o{ ControlAction     : includes
    ControlStructure  ||--o{ Feedback          : includes
    ControlStructure  ||--o| Controller        : includes
    ControlStructure  ||--o{ ControlledProcess : includes
    ControlStructure  ||--o| ProcessModel      : includes
    ControlStructure  ||--o| ControlAlgorithm  : includes

    Controller       ||--|| System          : is_a
    ControlAlgorithm ||--|| Function        : is_a
    ControlAlgorithm ||--|| Interface       : is_a
    ControlAlgorithm ||--|{ ControlAction   : Generates

    ControlledProcess ||--o| System       : Is
    ControlledProcess ||--o| Function     : Is
    ControlledProcess ||--o{ Feedback     : Issues

    ProcessModel ||--|| Function          : is_a
    ProcessModel ||--|{ Feedback          : Processes

    ControlAction ||--o| InTransition     : Causes
    ControlAction ||--o| OutTransition    : Causes
    Feedback      ||--o| InTransition     : Causes
    Feedback      ||--o| OutTransition    : Causes

    StateDiagram ||--o{ State            : Has
    State        ||--o{ Hazard           : May_be
    State        ||--o{ InTransition     : Has
    State        ||--o{ OutTransition    : Has

    System {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  SystemName
        string  SystemDescription
        string  Baseline
        enum    Criticality
        boolean Confidentiality
        boolean Integrity
        boolean Availability
        boolean Authenticity
        boolean NonRepudiation
        boolean Assurance
        boolean Trustworthy
        boolean Privacy
        string  ConfidentialityDescription
        string  IntegrityDescription
        string  AvailabilityDescription
        string  AuthenticityDescription
        string  NonRepudiationDescription
        string  AssuranceDescription
        string  TrustworthyDescription
        string  PrivacyDescription
    }

    Function {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  ShortTextIdentifier
        string  FunctionName
        string  FunctionDescription
        string  Baseline
        enum    Criticality
        boolean Confidentiality
        boolean Integrity
        boolean Availability
        boolean Authenticity
        boolean NonRepudiation
        boolean Assurance
        boolean Trustworthy
        boolean Privacy
        string  ConfidentialityDescription
        string  IntegrityDescription
        string  AvailabilityDescription
        string  AuthenticityDescription
        string  NonRepudiationDescription
        string  AssuranceDescription
        string  TrustworthyDescription
        string  PrivacyDescription
    }

    Interface {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  InterfaceName
        string  InterfaceDescription
        string  Baseline
        enum    Criticality
        boolean Confidentiality
        boolean Integrity
        boolean Availability
        boolean Authenticity
        boolean NonRepudiation
        boolean Assurance
        boolean Trustworthy
        boolean Privacy
        string  ConfidentialityDescription
        string  IntegrityDescription
        string  AvailabilityDescription
        string  AuthenticityDescription
        string  NonRepudiationDescription
        string  AssuranceDescription
        string  TrustworthyDescription
        string  PrivacyDescription
    }

    Asset {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  AssetName
        string  AssetDescription
        string  Baseline
        enum    Criticality
        boolean Confidentiality
        boolean Integrity
        boolean Availability
        boolean Authenticity
        boolean NonRepudiation
        boolean Assurance
        boolean Trustworthy
        boolean Privacy
        string  ConfidentialityDescription
        string  IntegrityDescription
        string  AvailabilityDescription
        string  AuthenticityDescription
        string  NonRepudiationDescription
        string  AssuranceDescription
        string  TrustworthyDescription
        string  PrivacyDescription
    }

    Constraint {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  ConstraintName
        string  ConstraintDescription
        string  Baseline
    }

    Requirement {
        string  TypeIdentifier
        int     LevelIdentifier
        string  AlphanumericIdentifier
        string  SystemHierarchy
        string  ShortTextIdentifier
        string  Baseline
        enum    Criticality
        boolean Confidentiality
        boolean Integrity
        boolean Availability
        boolean Authenticity
        boolean NonRepudiation
        boolean Assurance
        boolean Trustworthy
        boolean Privacy
        string  ConfidentialityDescription
        string  IntegrityDescription
        string  AvailabilityDescription
        string  AuthenticityDescription
        string  NonRepudiationDescription
        string  AssuranceDescription
        string  TrustworthyDescription
        string  PrivacyDescription
        string  RequirementText
        enum    VerificationMethod
        string  VerificationStatement
        enum    Imperative
        string  Actor
        string  Action
    }

    Environment {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  EnvironmentName
        string  EnvironmentDescription
        string  OperationalContext
        string  EnvironmentalConditions
        string  Baseline
    }

    Hazard {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  HName
        string  HDescription
        string  Baseline
        enum    Criticality
        boolean Confidentiality
        boolean Integrity
        boolean Availability
        boolean Authenticity
        boolean NonRepudiation
        boolean Assurance
        boolean Trustworthy
        boolean Privacy
        string  ConfidentialityDescription
        string  IntegrityDescription
        string  AvailabilityDescription
        string  AuthenticityDescription
        string  NonRepudiationDescription
        string  AssuranceDescription
        string  TrustworthyDescription
        string  PrivacyDescription
    }

    Loss {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  LName
        string  LDescription
        string  Baseline
        string  LossDescription
    }

    ControlStructure {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  StructureName
        string  StructureDescription
        string  Baseline
        string  DiagramURL
        enum    Criticality
        boolean Confidentiality
        boolean Integrity
        boolean Availability
        boolean Authenticity
        boolean NonRepudiation
        boolean Assurance
        boolean Trustworthy
        boolean Privacy
        string  ConfidentialityDescription
        string  IntegrityDescription
        string  AvailabilityDescription
        string  AuthenticityDescription
        string  NonRepudiationDescription
        string  AssuranceDescription
        string  TrustworthyDescription
        string  PrivacyDescription
    }

    Controller {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  ShortTextIdentifier
        string  ControllerName
        string  ControllerDescription
        string  Baseline
    }

    ControlAlgorithm {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  ShortTextIdentifier
        string  ControlAlgoName
        string  ControlAlgoDescription
        string  Baseline
    }

    ProcessModel {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  ShortTextIdentifier
        string  PMName
        string  PMDescription
        string  Baseline
    }

    ControlledProcess {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  ShortTextIdentifier
        string  CPName
        string  CPDescription
        string  Baseline
    }

    ControlAction {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  CAName
        string  CADescription
        string  Baseline
        enum    Criticality
        boolean Confidentiality
        boolean Integrity
        boolean Availability
        boolean Authenticity
        boolean NonRepudiation
        boolean Assurance
        boolean Trustworthy
        boolean Privacy
        string  ConfidentialityDescription
        string  IntegrityDescription
        string  AvailabilityDescription
        string  AuthenticityDescription
        string  NonRepudiationDescription
        string  AssuranceDescription
        string  TrustworthyDescription
        string  PrivacyDescription
        boolean Unsafe
        boolean Unsecure
    }

    Feedback {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  FBName
        string  FBDescription
        string  Baseline
        enum    Criticality
        boolean Confidentiality
        boolean Integrity
        boolean Availability
        boolean Authenticity
        boolean NonRepudiation
        boolean Assurance
        boolean Trustworthy
        boolean Privacy
        string  ConfidentialityDescription
        string  IntegrityDescription
        string  AvailabilityDescription
        string  AuthenticityDescription
        string  NonRepudiationDescription
        string  AssuranceDescription
        string  TrustworthyDescription
        string  PrivacyDescription
        string  Description
    }

    SafetySecurityControl {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  SCName
        string  SCDescription
        string  Baseline
        enum    Criticality
        boolean Confidentiality
        boolean Integrity
        boolean Availability
        boolean Authenticity
        boolean NonRepudiation
        boolean Assurance
        boolean Trustworthy
        boolean Privacy
        string  ConfidentialityDescription
        string  IntegrityDescription
        string  AvailabilityDescription
        string  AuthenticityDescription
        string  NonRepudiationDescription
        string  AssuranceDescription
        string  TrustworthyDescription
        string  PrivacyDescription
        string  Description
    }

    StateDiagram {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  SDName
        string  SDDescription
        string  Baseline
        string  DiagramURL
    }

    State {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  ShortTextIdentifier
        string  Baseline
        enum    Criticality
        boolean Confidentiality
        boolean Integrity
        boolean Availability
        boolean Authenticity
        boolean NonRepudiation
        boolean Assurance
        boolean Trustworthy
        boolean Privacy
        string  ConfidentialityDescription
        string  IntegrityDescription
        string  AvailabilityDescription
        string  AuthenticityDescription
        string  NonRepudiationDescription
        string  AssuranceDescription
        string  TrustworthyDescription
        string  PrivacyDescription
        string  State_Description
    }

    InTransition {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  InTransitionName
        string  InTransitionDescription
        string  Baseline
        string  In_Transition_Description
    }

    OutTransition {
        string  TypeIdentifier
        int     LevelIdentifier
        int     SequentialIdentifier
        string  SystemHierarchy
        string  OutTransitionName
        string  OutTransitionDescription
        string  Baseline
        string  Out_Transition_Description
    }
