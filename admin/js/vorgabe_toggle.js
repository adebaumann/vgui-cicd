(function($) {
    'use strict';
    
    $(document).ready(function() {
        // Add toggle buttons for each vorgabe inline
        $('.inline-group[data-inline-model="vorgabe"]').each(function() {
            var $group = $(this);
            var $headers = $group.find('h3');
            
            $headers.css('cursor', 'pointer').append(' <span class="toggle-hint">(klicken zum umschalten)</span>');
            
            $headers.on('click', function(e) {
                e.preventDefault();
                var $inline = $(this).closest('.inline-related');
                $inline.find('.collapse').toggleClass('collapsed');
            });
        });
        
        // Highlight active vorgabe when editing
        $('.inline-group[data-inline-model="vorgabe"] .inline-related').on('click', function() {
            $('.inline-group[data-inline-model="vorgabe"] .inline-related').removeClass('active-edit');
            $(this).addClass('active-edit');
        });
    });
})(django.jQuery);