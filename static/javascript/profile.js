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

function follow( userid ){
    fetch(window.location.origin + '/follow/' + userid)
    .then((response) => response.json())
    .then((body) => {
        if (body['response'] == 'successfully followed') {
            $('#follow').val('following').attr("disabled", "disabled")
        }
    })
}

function unfollow( userid ){
    fetch(window.location.origin + '/unfollow/' + userid)
    .then((response) => response.json())
    .then((body) => {
        if (body['response'] == 'successfully unfollowed') {
            $('#unfollow').val('unfollowed').attr("disabled", "disabled")
        }
    })
}
