document.addEventListener('DOMContentLoaded', () => {
  try {
    if (typeof frescoesData === 'undefined' || !Array.isArray(frescoesData.features)) {
      throw new Error('frescoesData is missing or malformed');
    }
    initMap(frescoesData.features);
  } catch (err) {
    console.error('Failed to initialize the fresco map:', err);
    const mapEl = document.getElementById('map-container');
    if (mapEl) {
      mapEl.innerHTML = '<div class="load-error">Couldn\u2019t load the fresco data. Try refreshing the page.</div>';
    }
  }
});

function initMap(features) {

  const prefersReducedMotion = window.matchMedia
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const baseCultureColors = { Minoan: '#a8354b', Mycenaean: '#8a6a1c', Cycladic: '#2f6f8f' };
  const fallbackPalette = ['#5b7f37', '#7d4f9e', '#c1622d', '#3c8f7a', '#8f4a6b'];
  const assignedColors = {};

  function getCultureColor(culture) {
    if (baseCultureColors[culture]) return baseCultureColors[culture];
    if (!assignedColors[culture]) {
      const used = Object.keys(assignedColors).length;
      assignedColors[culture] = fallbackPalette[used % fallbackPalette.length];
    }
    return assignedColors[culture];
  }

  const map = L.map('map-container', {
    zoomControl: false,
    zoomAnimation: !prefersReducedMotion,
    markerZoomAnimation: !prefersReducedMotion,
    fadeAnimation: !prefersReducedMotion
  }).setView([36.6, 24.5], 7);

  L.control.zoom({ position: 'bottomright' }).addTo(map);

  map.setMaxBounds([[28, 5], [48, 35]]);
  map.setMinZoom(5);

  if (L.control.fullscreen) {
    L.control.fullscreen({ position: 'topright' }).addTo(map);
  }

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  let markerCluster = L.markerClusterGroup();
  map.addLayer(markerCluster);

  const legendEl = document.getElementById('legend-items');
  const visibleCountEl = document.getElementById('visible-count');
  const statsNounEl = document.getElementById('stats-noun');
  const searchInput = document.getElementById('search-input');
  const resultsListEl = document.getElementById('results-list');
  const timelineWrap = document.getElementById('timeline-filter-wrap');
  const timelineMinInput = document.getElementById('timeline-min');
  const timelineMaxInput = document.getElementById('timeline-max');
  const timelineRangeFill = document.getElementById('timeline-range-fill');
  const timelineMinLabel = document.getElementById('timeline-min-label');
  const timelineMaxLabel = document.getElementById('timeline-max-label');
  const timelineReset = document.getElementById('timeline-reset');
  const browseAllToggle = document.getElementById('browse-all-toggle');
  const clearFiltersBtn = document.getElementById('clear-filters');

  let selectedCulture = 'all';

  let browseAllActive = false;

  let timelineBoundsMin = null;
  let timelineBoundsMax = null;

  const markersById = new Map();

  const lightbox = document.createElement('div');
  lightbox.className = 'lightbox';
  lightbox.hidden = true;
  lightbox.setAttribute('role', 'dialog');
  lightbox.setAttribute('aria-modal', 'true');
  lightbox.setAttribute('aria-label', 'Enlarged fresco image');

  const lightboxImg = document.createElement('img');
  lightboxImg.className = 'lightbox-img';
  lightbox.appendChild(lightboxImg);

  const lightboxCaption = document.createElement('div');
  lightboxCaption.className = 'lightbox-caption';
  lightbox.appendChild(lightboxCaption);

  const lightboxClose = document.createElement('button');
  lightboxClose.type = 'button';
  lightboxClose.className = 'lightbox-close';
  lightboxClose.setAttribute('aria-label', 'Close enlarged image');
  lightboxClose.textContent = '\u00d7';
  lightbox.appendChild(lightboxClose);

  document.body.appendChild(lightbox);

  let lightboxReturnFocus = null;

  function openLightbox(url, alt, triggerEl) {
    lightboxImg.src = url;
    lightboxImg.alt = alt || '';
    lightboxCaption.textContent = alt || '';
    lightboxReturnFocus = triggerEl || null;
    lightbox.hidden = false;
    lightboxClose.focus();
    document.addEventListener('keydown', onLightboxKeydown);
  }

  function closeLightbox() {
    lightbox.hidden = true;
    lightboxImg.src = '';
    document.removeEventListener('keydown', onLightboxKeydown);
    if (lightboxReturnFocus) {
      lightboxReturnFocus.focus();
      lightboxReturnFocus = null;
    }
  }

  function onLightboxKeydown(e) {
    if (e.key === 'Escape') {
      closeLightbox();
    } else if (e.key === 'Tab') {
      e.preventDefault();
      lightboxClose.focus();
    }
  }

  lightboxClose.addEventListener('click', closeLightbox);
  lightbox.addEventListener('click', (e) => {
    if (e.target === lightbox) closeLightbox();
  });

  function debounce(fn, delayMs) {
    let timeoutId;
    return (...args) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn(...args), delayMs);
    };
  }

  function getEnlargedUrl(url) {
    if (/[?&]width=\d+/.test(url)) {
      return url.replace(/([?&]width=)\d+/, '$11200');
    }
    return url;
  }

  function formatYear(year) {
    if (year < 0) return `${Math.abs(year)} BCE`;
    if (year === 0) return '0';
    return `${year} CE`;
  }

  function updateTimelineVisuals() {
    const min = timelineBoundsMin;
    const max = timelineBoundsMax;
    const span = max - min || 1;
    const minVal = Number(timelineMinInput.value);
    const maxVal = Number(timelineMaxInput.value);
    const leftPct = ((minVal - min) / span) * 100;
    const rightPct = ((maxVal - min) / span) * 100;
    timelineRangeFill.style.left = `${leftPct}%`;
    timelineRangeFill.style.width = `${Math.max(rightPct - leftPct, 0)}%`;
    timelineMinLabel.textContent = formatYear(minVal);
    timelineMaxLabel.textContent = formatYear(maxVal);
    timelineMinInput.setAttribute('aria-valuetext', formatYear(minVal));
    timelineMaxInput.setAttribute('aria-valuetext', formatYear(maxVal));
  }

  function setupTimelineSlider() {
    const starts = features.map(f => f.properties.dateStart).filter(v => typeof v === 'number');
    const ends = features.map(f => f.properties.dateEnd).filter(v => typeof v === 'number');

    if (starts.length === 0 || ends.length === 0) {
      timelineWrap.hidden = true;
      return;
    }

    timelineBoundsMin = Math.min(...starts);
    timelineBoundsMax = Math.max(...ends);

    const step = 25;
    [timelineMinInput, timelineMaxInput].forEach(input => {
      input.min = timelineBoundsMin;
      input.max = timelineBoundsMax;
      input.step = step;
    });
    timelineMinInput.value = timelineBoundsMin;
    timelineMaxInput.value = timelineBoundsMax;

    function clampAndRender(moved) {
      const minGap = step;
      let minVal = Number(timelineMinInput.value);
      let maxVal = Number(timelineMaxInput.value);
      if (minVal > maxVal - minGap) {
        if (moved === 'min') {
          minVal = maxVal - minGap;
          timelineMinInput.value = minVal;
        } else {
          maxVal = minVal + minGap;
          timelineMaxInput.value = maxVal;
        }
      }
      updateTimelineVisuals();
      renderMarkers();
    }

    timelineMinInput.addEventListener('input', () => clampAndRender('min'));
    timelineMaxInput.addEventListener('input', () => clampAndRender('max'));

    timelineMinInput.addEventListener('pointerdown', () => {
      timelineMinInput.style.zIndex = 3;
      timelineMaxInput.style.zIndex = 2;
    });
    timelineMaxInput.addEventListener('pointerdown', () => {
      timelineMaxInput.style.zIndex = 3;
      timelineMinInput.style.zIndex = 2;
    });

    timelineReset.addEventListener('click', () => {
      timelineMinInput.value = timelineBoundsMin;
      timelineMaxInput.value = timelineBoundsMax;
      updateTimelineVisuals();
      renderMarkers();
    });

    updateTimelineVisuals();
  }

  function populateFiltersAndLegend() {
    const cultures = [...new Set(features.map(f => f.properties.culture).filter(Boolean))].sort();

    cultures.forEach(culture => {
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'legend-item';
      item.setAttribute('aria-pressed', 'false');
      const swatch = document.createElement('span');
      swatch.className = 'swatch';
      swatch.style.background = getCultureColor(culture);
      swatch.setAttribute('aria-hidden', 'true');
      item.appendChild(swatch);
      item.appendChild(document.createTextNode(culture));
      item.addEventListener('click', () => {
        selectedCulture = (selectedCulture === culture) ? 'all' : culture;
        renderMarkers();
      });
      legendEl.appendChild(item);
    });
  }

  function updateLegendPressedState() {
    legendEl.querySelectorAll('.legend-item').forEach(btn => {
      const culture = btn.textContent.trim();
      btn.setAttribute('aria-pressed', String(culture === selectedCulture));
    });
  }

  function makeIcon(culture) {
    const color = getCultureColor(culture);
    return L.divIcon({
      className: '',
      html: `<div style="width:16px;height:16px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.4);"></div>`,
      iconSize: [16, 16],
      iconAnchor: [8, 8],
      popupAnchor: [0, -8]
    });
  }

  function buildPopup(props) {
    const color = getCultureColor(props.culture);
    const card = document.createElement('div');
    card.className = 'popup-card';

    const hasRealImage = props.imageUrl && /^https?:\/\//i.test(props.imageUrl);

    if (hasRealImage) {
      const img = document.createElement('img');
      img.src = props.imageUrl;
      img.alt = props.title || '';
      img.className = 'popup-thumb';
      img.tabIndex = 0;
      img.setAttribute('role', 'button');
      img.setAttribute('aria-label', `Enlarge image of ${props.title || 'this fresco'}`);
      const openThisLightbox = () => openLightbox(getEnlargedUrl(props.imageUrl), props.title, img);
      img.addEventListener('click', openThisLightbox);
      img.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          openThisLightbox();
        }
      });
      img.addEventListener('error', () => {
        const fallback = document.createElement('div');
        fallback.className = 'popup-image-pending';
        fallback.style.background = color;
        fallback.textContent = 'Image failed to load';
        img.replaceWith(fallback);
      }, { once: true });
      card.appendChild(img);
    } else {
      const pending = document.createElement('div');
      pending.className = 'popup-image-pending';
      pending.style.background = color;
      pending.textContent = 'Image pending';
      card.appendChild(pending);
    }

    if (props.imageAttribution) {
      const attr = props.imageAttribution;
      const credit = document.createElement('div');
      credit.className = 'image-credit';
      credit.appendChild(document.createTextNode(`Photo: ${attr.photographer || 'Unknown'}, `));

      if (attr.licenseUrl) {
        const licenseLink = document.createElement('a');
        licenseLink.href = attr.licenseUrl;
        licenseLink.target = '_blank';
        licenseLink.rel = 'noopener noreferrer';
        licenseLink.textContent = attr.license || 'license';
        credit.appendChild(licenseLink);
      } else if (attr.license) {
        credit.appendChild(document.createTextNode(attr.license));
      }

      if (attr.sourceUrl) {
        credit.appendChild(document.createTextNode(' \u00b7 '));
        const sourceLink = document.createElement('a');
        sourceLink.href = attr.sourceUrl;
        sourceLink.target = '_blank';
        sourceLink.rel = 'noopener noreferrer';
        sourceLink.textContent = 'source';
        credit.appendChild(sourceLink);
      }

      card.appendChild(credit);
    }

    const badge = document.createElement('span');
    badge.className = 'culture-badge';
    badge.style.background = color;
    badge.textContent = props.culture || '';
    card.appendChild(badge);

    const h3 = document.createElement('h3');
    h3.textContent = props.title || '';
    card.appendChild(h3);

    function addField(label, value) {
      if (!value) return;
      const p = document.createElement('p');
      const strong = document.createElement('strong');
      strong.textContent = label + ': ';
      p.appendChild(strong);
      p.appendChild(document.createTextNode(value));
      card.appendChild(p);
    }
    addField('Period', props.period);
    addField('Site', props.site);
    addField('Museum', props.currentMuseum);
    addField('Citation', props.sourceCitation);

    if (props.description) {
      const desc = document.createElement('div');
      desc.className = 'desc';
      desc.textContent = props.description;
      card.appendChild(desc);
    }

    return card;
  }

  function renderMarkers() {
    markerCluster.clearLayers();
    markersById.clear();
    resultsListEl.innerHTML = '';

    const searchTerm = searchInput.value.trim().toLowerCase();
    const timelineActive = timelineBoundsMin !== null;
    const timelineMinVal = timelineActive ? Number(timelineMinInput.value) : null;
    const timelineMaxVal = timelineActive ? Number(timelineMaxInput.value) : null;

    const filtered = features.filter(f => {
      const p = f.properties;
      const matchesCulture = (selectedCulture === 'all' || p.culture === selectedCulture);
      const matchesSearch = !searchTerm || [p.title, p.site, p.region, p.theme, p.culture, p.description]
        .filter(Boolean)
        .some(field => field.toLowerCase().includes(searchTerm));
      const matchesTimeline = !timelineActive
        || typeof p.dateStart !== 'number'
        || typeof p.dateEnd !== 'number'
        || (p.dateStart <= timelineMaxVal && p.dateEnd >= timelineMinVal);
      return matchesCulture && matchesSearch && matchesTimeline;
    });

    filtered.forEach(f => {
      const [lng, lat] = f.geometry.coordinates;
      const marker = L.marker([lat, lng], {
        icon: makeIcon(f.properties.culture),
        title: `${f.properties.title} \u2014 ${f.properties.culture}`
      }).bindPopup(buildPopup(f.properties));
      marker.frescoId = f.properties.id;
      markerCluster.addLayer(marker);
      markersById.set(f.properties.id, marker);
    });

    visibleCountEl.textContent = filtered.length;
    statsNounEl.textContent = filtered.length === 1 ? 'fresco' : 'frescoes';

    updateLegendPressedState();

    const timelineNarrowed = timelineActive
      && (timelineMinVal > timelineBoundsMin || timelineMaxVal < timelineBoundsMax);
    const anyFilterActive = selectedCulture !== 'all' || searchTerm !== '' || timelineNarrowed;
    clearFiltersBtn.disabled = !anyFilterActive;

    if (searchTerm || browseAllActive) {
      renderResultsList(filtered);
    }
  }

  function renderResultsList(matches) {
    if (matches.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'result-item';
      empty.textContent = 'No frescoes match your search.';
      resultsListEl.appendChild(empty);
      return;
    }

    matches.forEach(f => {
      const p = f.properties;
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'result-item';

      const swatch = document.createElement('span');
      swatch.className = 'swatch';
      swatch.style.background = getCultureColor(p.culture);
      item.appendChild(swatch);

      const textWrap = document.createElement('span');
      textWrap.className = 'result-text';
      const titleEl = document.createElement('span');
      titleEl.textContent = p.title;
      const siteEl = document.createElement('span');
      siteEl.className = 'result-site';
      siteEl.textContent = p.site || '';
      textWrap.appendChild(titleEl);
      textWrap.appendChild(siteEl);
      item.appendChild(textWrap);

      item.addEventListener('click', () => goToFresco(p.id));
      resultsListEl.appendChild(item);
    });
  }

  function goToFresco(id) {
    const marker = markersById.get(id);
    if (!marker) return;
    map.setView(marker.getLatLng(), Math.max(map.getZoom(), 11), { animate: !prefersReducedMotion });
    markerCluster.zoomToShowLayer(marker, () => marker.openPopup());
  }

  map.on('popupopen', (e) => {
    const marker = e.popup._source;
    if (marker && marker.frescoId) {
      history.replaceState(null, '', `#${marker.frescoId}`);
    }
  });

  map.on('popupclose', () => {
    if (!lightbox.hidden) closeLightbox();
  });

  function openFromHash() {
    const id = decodeURIComponent(location.hash.slice(1));
    if (id && markersById.has(id)) {
      goToFresco(id);
    }
  }

  window.addEventListener('hashchange', openFromHash);

  clearFiltersBtn.addEventListener('click', () => {
    selectedCulture = 'all';
    searchInput.value = '';
    if (timelineBoundsMin !== null) {
      timelineMinInput.value = timelineBoundsMin;
      timelineMaxInput.value = timelineBoundsMax;
      updateTimelineVisuals();
    }
    renderMarkers();
    searchInput.focus();
  });

  browseAllToggle.addEventListener('click', () => {
    browseAllActive = !browseAllActive;
    browseAllToggle.setAttribute('aria-pressed', String(browseAllActive));
    browseAllToggle.textContent = browseAllActive
      ? 'Hide full list'
      : 'List all visible frescoes';
    renderMarkers();
  });

  resultsListEl.addEventListener('keydown', (e) => {
    const items = Array.from(resultsListEl.querySelectorAll('.result-item'));
    const currentIndex = items.indexOf(document.activeElement);
    if (currentIndex === -1) return;

    let nextIndex = null;
    if (e.key === 'ArrowDown') nextIndex = (currentIndex + 1) % items.length;
    else if (e.key === 'ArrowUp') nextIndex = (currentIndex - 1 + items.length) % items.length;
    else if (e.key === 'Home') nextIndex = 0;
    else if (e.key === 'End') nextIndex = items.length - 1;
    else if (e.key === 'Escape') { searchInput.focus(); return; }

    if (nextIndex !== null) {
      e.preventDefault();
      items[nextIndex].focus();
    }
  });

  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') {
      const first = resultsListEl.querySelector('.result-item');
      if (first) {
        e.preventDefault();
        first.focus();
      }
    }
  });

  populateFiltersAndLegend();
  setupTimelineSlider();

  searchInput.addEventListener('input', debounce(renderMarkers, 150));

  renderMarkers();
  openFromHash();
}