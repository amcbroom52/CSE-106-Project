function update_bio() {
    bio = $('#bio').val()

    const package = {
        new_bio: bio
    }

    fetch(window.location.origin + '/update_bio', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(package)
    })
}