window.addEventListener('load', function () {
    setTimeout(() => {
        const vorgabenBlocks = document.querySelectorAll('.djn-dynamic-form-Standards-vorgabe');
        console.log("Found", vorgabenBlocks.length, "Vorgaben blocks");

        vorgabenBlocks.forEach((block, index) => {
            const header = document.createElement('div');
            header.className = 'vorgabe-toggle-header';
            header.innerHTML = `▼ Vorgabe ${index + 1}`;
            header.style.cursor = 'pointer';

            block.parentNode.insertBefore(header, block);

            header.addEventListener('click', () => {
                const isHidden = block.style.display === 'none';
                block.style.display = isHidden ? '' : 'none';
                header.innerHTML = `${isHidden ? '▼' : '▶'} Vorgabe ${index + 1}`;
            });
        });
    }, 500); // wait 500ms to allow nested inlines to render
});
