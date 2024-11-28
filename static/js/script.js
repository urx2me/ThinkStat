function toggleRegion(region) {
    const setA = document.getElementById('setA');
    const setB = document.getElementById('setB');
    const vennBackground = document.querySelector('.venn-diagram');

    // Reset to default colors
    const resetColors = () => {
        setA.style.fill = 'lightblue';
        setB.style.fill = 'lightpink';
        setA.setAttribute('opacity', '0.8');
        setB.setAttribute('opacity', '0.8');
        setA.style.mixBlendMode = 'normal';  
        setB.style.mixBlendMode = 'normal';  
        vennBackground.style.background = 'white';
    };

    // Handle Union
    if (region === 'union') {
        const unionCheckbox = document.getElementById('unionCheckbox');
        if (unionCheckbox.checked) {
            setA.style.fill = 'purple';
            setB.style.fill = 'purple';
            setA.setAttribute('opacity', '0.5');
            setB.setAttribute('opacity', '0.5');
        } else {
            resetColors();
        }
    }

    // Handle Intersection 
    if (region === 'intersection') {
        const intersectionCheckbox = document.getElementById('intersectionCheckbox');
        if (intersectionCheckbox.checked) {
            // Retain original colors for A and B
            setA.style.fill = 'lightblue';
            setB.style.fill = 'lightpink';
            setA.setAttribute('opacity', '0.8');
            setB.setAttribute('opacity', '0.8');
            
            // Apply a blending effect to the intersection
            setA.style.mixBlendMode = 'multiply';  
            setB.style.mixBlendMode = 'multiply';  
        } else {
            resetColors(); // Reset everything to default if intersection checkbox is unchecked
        }
    }

    // Handle Complement 
    if (region === 'complement') {
        const complementCheckbox = document.getElementById('complementCheckbox');
        if (complementCheckbox.checked) {
            vennBackground.style.background = 'lightgray';
            setA.style.fill = 'lightblue';
            setB.style.fill = 'lightpink';
        } else {
            resetColors();
        }
    }
}