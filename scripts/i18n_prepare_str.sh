
# Write the palisades translation information to Palisades.pot.

find palisades -name "*.py" | xargs xgettext -d Palisades -o i18n/Palisades.pot --language=Python


# Convert Palisades.pot to the language-specific .po files, merging them with
# the older versions of the same file.
pushd i18n
mkdir merged_po

for locale in "es" "en" "de"
do
    # merge the new file with the existing one, saving to the merged_po folder
    msgmerge $locale.po Palisades.pot > merged_po/$locale.po

    # copy the merged_po file to the original location.
    cp merged_po/$locale.po $locale.po
done

rm -r merged_po
popd

