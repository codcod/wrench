# JSON data wrangling

## Sonar API: `measures/component`

Quality gate level for a component:

    jq '.component.measures[] | select(.metric=="quality_gate_details") | .value' |sed 's/\\//g;s/"*$//;s/^"//' |jq '.level'
