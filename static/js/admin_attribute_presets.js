/**
 * Admin helper: auto-populate ProductAttribute inline rows
 * based on the selected product category.
 *
 * Adds a "Load presets" button above the Attributes inline.
 * When clicked it inserts rows for common attributes for that
 * category so the admin only needs to fill in the values.
 */
'use strict';

var PRESETS = {
    'clothing': [
        'Color', 'Secondary Color', 'Material / Fabric', 'Fabric Composition',
        'Fit', 'Pattern', 'Sleeve Length', 'Collar / Neckline',
        'Care Instructions', 'Season', 'Occasion',
        'Country of Origin', 'Gender'
    ],
    'mens-fashion': [
        'Color', 'Material / Fabric', 'Fit', 'Pattern',
        'Sleeve Length', 'Collar Type', 'Care Instructions',
        'Season', 'Occasion', 'Country of Origin'
    ],
    'womens-fashion': [
        'Color', 'Material / Fabric', 'Fit', 'Pattern',
        'Neckline', 'Sleeve Length', 'Care Instructions',
        'Season', 'Occasion', 'Country of Origin'
    ],
    'electronics': [
        'Brand Model', 'Processor', 'RAM', 'Storage',
        'Display Size', 'Resolution', 'Battery Life',
        'Operating System', 'Connectivity', 'Colour', 'Warranty'
    ],
    'jewellery': [
        'Metal Type', 'Metal Purity', 'Stone Type', 'Stone Colour',
        'Stone Cut', 'Clasp Type', 'Length / Size',
        'Weight (g)', 'Country of Origin', 'Certificate'
    ],
};

/* fallback generic set shown when no category matches */
var GENERIC_PRESETS = [
    'Color', 'Material', 'Dimensions', 'Weight',
    'Country of Origin', 'Warranty'
];

django.jQuery(document).ready(function ($) {

    /* Find the attribute inline group */
    function getAttrInline() {
        return $('.inline-group').filter(function () {
            return $(this).find('h2').text().toLowerCase().indexOf('attribute') >= 0;
        });
    }

    /* Slugify a string to compare against preset keys */
    function slugify(s) {
        return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    }

    /* Add a single row via the inline "Add another" link, then fill the name */
    function addRow(inlineEl, attrName) {
        var addLink = inlineEl.find('.add-row a');
        if (!addLink.length) return;
        addLink.trigger('click');
        /* last non-empty-form row just added */
        var rows = inlineEl.find('tr.form-row').not('.empty-form');
        var lastRow = rows.last();
        lastRow.find('input[id$="-name"]').val(attrName);
    }

    /* Build and inject the preset button */
    function injectButton() {
        var inlineEl = getAttrInline();
        if (!inlineEl.length || inlineEl.find('#load-attr-presets').length) return;

        var btn = $('<button>', {
            type: 'button',
            id: 'load-attr-presets',
            text: '📋  Load attribute presets for selected category',
            css: {
                margin: '0 0 10px 0',
                padding: '6px 14px',
                cursor: 'pointer',
                background: '#417690',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                fontSize: '13px',
            }
        });

        /* insert before the inline's table */
        inlineEl.find('.tabular').before(btn);

        btn.on('click', function () {
            var catText = slugify($('#id_category option:selected').text());
            var attrs = null;

            /* exact match first, then substring */
            if (PRESETS[catText]) {
                attrs = PRESETS[catText];
            } else {
                $.each(PRESETS, function (key) {
                    if (!attrs && (catText.indexOf(key) >= 0 || key.indexOf(catText) >= 0)) {
                        attrs = PRESETS[key];
                    }
                });
            }
            if (!attrs) attrs = GENERIC_PRESETS;

            /* clear existing empty rows first */
            inlineEl.find('tr.form-row').not('.empty-form').each(function () {
                var nameInput = $(this).find('input[id$="-name"]');
                var valInput  = $(this).find('input[id$="-value"]');
                if (!nameInput.val() && !valInput.val()) {
                    $(this).find('.inline-deletelink').trigger('click');
                }
            });

            /* add a row per preset attribute */
            $.each(attrs, function (i, name) {
                addRow(inlineEl, name);
            });

            btn.text('✅  Presets loaded — fill in the values below');
            btn.css('background', '#28a745');
        });
    }

    /* Run on page load and whenever category changes */
    injectButton();
    $('#id_category').on('change', function () {
        /* reset button label if category changes */
        $('#load-attr-presets')
            .text('📋  Load attribute presets for selected category')
            .css('background', '#417690');
    });
});
