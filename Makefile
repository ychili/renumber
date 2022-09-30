OUTDIR := data
PYTHON ?= /usr/bin/env python3

$(OUTDIR)/renumber.1.gz: $(OUTDIR)/renumber.1
	gzip -9 -c $(OUTDIR)/renumber.1 > $(OUTDIR)/renumber.1.gz

$(OUTDIR)/renumber.1: renumber.1.in renumber.py | $(OUTDIR)
	sed -e "s/CURRENT_DATE/$$(date -u +%Y-%m-%d)/" \
		-e "s/VERSION_NUMBER/renumber $$($(PYTHON) scripts/extract_attr.py __version__ renumber.py)/" \
		renumber.1.in > $(OUTDIR)/renumber.1

$(OUTDIR):
	mkdir $(OUTDIR)

clean:
	rm -f $(OUTDIR)/*

.PHONY: clean
