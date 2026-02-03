#!/bin/bash
# Bulk recepten digitalisatie tool
# Gebruik: ./digitize.sh <command> [args]

set -e

# Laad .env als aanwezig
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

CMD="uv run python -m boodschappenagent.cli.digitize"

case "$1" in
    process|p)
        # ./digitize.sh process <pdf> [batch-id]
        # ./digitize.sh p scans/batch.pdf mybatch
        PDF="${2:?Geef een PDF pad op}"
        BATCH_ID="$3"
        if [ -n "$BATCH_ID" ]; then
            $CMD process "$PDF" --batch-id "$BATCH_ID" --dpi 150 --delay 0.5
        else
            $CMD process "$PDF" --dpi 150 --delay 0.5
        fi
        ;;
    status|s)
        # ./digitize.sh status <batch-id>
        # ./digitize.sh s mybatch
        BATCH_ID="${2:?Geef een batch-id op}"
        $CMD status "$BATCH_ID"
        ;;
    review|r)
        # ./digitize.sh review <batch-id> <recipe>
        # ./digitize.sh r mybatch 01
        BATCH_ID="${2:?Geef een batch-id op}"
        RECIPE="${3:?Geef een recept nummer op (bijv. 01)}"
        $CMD review "$BATCH_ID" --recipe "$RECIPE"
        ;;
    accept|a)
        # ./digitize.sh accept <batch-id> <recipe|--all>
        # ./digitize.sh a mybatch 01
        # ./digitize.sh a mybatch --all
        BATCH_ID="${2:?Geef een batch-id op}"
        RECIPE="$3"
        if [ "$RECIPE" = "--all" ] || [ "$RECIPE" = "-a" ]; then
            $CMD accept "$BATCH_ID" --all
        elif [ -n "$RECIPE" ]; then
            $CMD accept "$BATCH_ID" --recipe "$RECIPE"
        else
            echo "Geef een recept nummer of --all op"
            exit 1
        fi
        ;;
    list|l)
        # ./digitize.sh list - toon alle batches
        echo "Batches in data/recipes/draft/:"
        ls -1 data/recipes/draft/ 2>/dev/null | grep -v "^_" || echo "  (geen batches)"
        ;;
    help|h|"")
        echo "Bulk recepten digitalisatie tool"
        echo ""
        echo "Gebruik: ./digitize.sh <command> [args]"
        echo ""
        echo "Commands:"
        echo "  process|p <pdf> [batch-id]    Verwerk een PDF batch"
        echo "  status|s  <batch-id>          Toon status van een batch"
        echo "  review|r  <batch-id> <nr>     Review een recept (bijv. 01)"
        echo "  accept|a  <batch-id> <nr|--all>  Accepteer recept(en)"
        echo "  list|l                        Toon alle batches"
        echo ""
        echo "Voorbeelden:"
        echo "  ./digitize.sh p scans/nieuwe-recepten.pdf"
        echo "  ./digitize.sh s scan-20260203"
        echo "  ./digitize.sh r scan-20260203 01"
        echo "  ./digitize.sh a scan-20260203 01"
        echo "  ./digitize.sh a scan-20260203 --all"
        ;;
    *)
        echo "Onbekend command: $1"
        echo "Gebruik: ./digitize.sh help"
        exit 1
        ;;
esac
