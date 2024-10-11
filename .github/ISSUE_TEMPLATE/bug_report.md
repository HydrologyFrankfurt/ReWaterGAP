name: Bug Report
description: Create a report to help us improve
title: "BUG: "
labels: [Bug]

body:
  - type: textarea
    id: example
    attributes:
      label: Issue Description
      description: >
        What is the nature of the Bug you encountered?
      placeholder: Describe the Bug here.
    
      render: python
    validations:
      required: true
  - type: textarea
    id: problem
    attributes:
      label: Issue Description
      description: >
        Please provide a description of the issue shown in the reproducible example.
    validations:
      required: true
  - type: textarea
    id: expected-behavior
    attributes:
      label: Expected Behavior
      description: >
        Please describe or show a code example of the expected behavior.
    validations:
      required: true
  - type: textarea
    id: version
    attributes:
      label: Installed Versions
      description: >
        Please paste the output of ``pd.show_versions()``
      value: >
        <details>


        Replace this line with the output of pd.show_versions()


        </details>
    validations:
      required: true
