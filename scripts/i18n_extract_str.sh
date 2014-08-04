# Write the palisades translation information to Palisades.pot.

find palisades -name "*.py" | xargs xgettext -d Palisades -o i18n/Palisades.pot --language=Python
