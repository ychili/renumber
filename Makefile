OUTDIR = data
TMPFILE = /tmp/renumber_version.tmp

$(OUTDIR)/renumber.1.gz: $(OUTDIR)/renumber.1
	gzip -9 -c $(OUTDIR)/renumber.1 > $(OUTDIR)/renumber.1.gz

$(OUTDIR)/renumber.1: renumber.1.in renumber.py | $(OUTDIR)
	python3 scripts/extract_attr.py "__version__" renumber.py > $(TMPFILE)
	sed -e "s/CURRENT_DATE/$$(date -u +%Y-%m-%d)/" -e "s/VERSION_NUMBER/renumber `cat $(TMPFILE)`/" renumber.1.in > $(OUTDIR)/renumber.1

$(OUTDIR):
	mkdir $(OUTDIR)

clean:
	rm data/*
