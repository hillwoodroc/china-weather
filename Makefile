.DEFAULT_GOAL := run

PREFIX ?= /usr/local
DATADIR = $(PREFIX)/share/china-weather
ICONDIR = $(PREFIX)/share/icons/hicolor/scalable/apps

.PHONY: run test install uninstall translations update-po

LANGUAGES = zh_CN zh_TW en
CATALOGS = $(foreach lang,$(LANGUAGES),china_weather/locale/$(lang)/LC_MESSAGES/china-weather.mo)

translations: $(CATALOGS)

china_weather/locale/%/LC_MESSAGES/china-weather.mo: po/%.po
	mkdir -p $(@D)
	msgfmt --check --check-format -o $@ $<

po/china-weather.pot: $(wildcard china_weather/*.py)
	xgettext --language=Python --from-code=UTF-8 --keyword=_ --keyword=N_ --keyword=weather_message:1c,2 --package-name=China-Weather --output=$@ $^

update-po: po/china-weather.pot
	for lang in $(LANGUAGES); do msgmerge --update --backup=none po/$$lang.po $<; done
run: translations
	python3 -m china_weather

test: translations
	python3 -m unittest discover -s tests -v

install: translations
	install -d $(DESTDIR)$(DATADIR)/china_weather $(DESTDIR)$(PREFIX)/bin $(DESTDIR)$(PREFIX)/share/applications
	install -m644 china_weather/*.py $(DESTDIR)$(DATADIR)/china_weather/
	for lang in $(LANGUAGES); do \
		install -d $(DESTDIR)$(DATADIR)/china_weather/locale/$$lang/LC_MESSAGES; \
		install -m644 china_weather/locale/$$lang/LC_MESSAGES/china-weather.mo $(DESTDIR)$(DATADIR)/china_weather/locale/$$lang/LC_MESSAGES/; \
	done
	sed 's|@DATADIR@|$(DATADIR)|g' data/launcher.in > $(DESTDIR)$(PREFIX)/bin/china-weather
	chmod 755 $(DESTDIR)$(PREFIX)/bin/china-weather
	install -m755 china-weather $(DESTDIR)$(DATADIR)/china-weather
	install -m644 data/*.desktop $(DESTDIR)$(PREFIX)/share/applications/
	install -d $(DESTDIR)$(ICONDIR)
	install -m644 data/io.github.hillwood.ChinaWeather.svg $(DESTDIR)$(ICONDIR)/

uninstall:
	rm -rf $(DESTDIR)$(DATADIR)
	rm -f $(DESTDIR)$(PREFIX)/bin/china-weather $(DESTDIR)$(PREFIX)/share/applications/io.github.hillwood.ChinaWeather.desktop $(DESTDIR)$(ICONDIR)/io.github.hillwood.ChinaWeather.svg
