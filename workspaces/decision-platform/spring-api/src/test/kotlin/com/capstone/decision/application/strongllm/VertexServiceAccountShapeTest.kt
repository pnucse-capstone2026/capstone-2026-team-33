package com.capstone.decision.application.strongllm

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.security.KeyPairGenerator
import java.util.Base64

private val validPrivateKey by lazy {
    val keyPair = KeyPairGenerator.getInstance("RSA").apply { initialize(2048) }.generateKeyPair()
    val pem = Base64.getMimeEncoder(64, byteArrayOf('\n'.code.toByte())).encodeToString(keyPair.private.encoded)
    "-----BEGIN PRIVATE KEY-----\n$pem\n-----END PRIVATE KEY-----\n"
}

private val syntheticServiceAccountJson by lazy {
    """{"type":"service_account","project_id":"mars-test-dummy","private_key_id":"0123456789abcdef",""" +
        """"private_key":"${validPrivateKey.replace("\n", "\\n")}",""" +
        """"client_email":"dummy@mars-test-dummy.iam.gserviceaccount.com","token_uri":"https://oauth2.googleapis.com/token"}"""
}

internal fun syntheticVertexServiceAccountB64(): String =
    Base64.getEncoder().encodeToString(syntheticServiceAccountJson.toByteArray())

class VertexServiceAccountShapeTest {
    private fun encode(json: String) = Base64.getEncoder().encodeToString(json.toByteArray())

    @Test
    fun `a canonical base64 service account is accepted and shows its key id tail`() {
        val encoded = encode(syntheticServiceAccountJson)
        assertThat(VertexServiceAccountShape.isValid(encoded)).isTrue()
        assertThat(VertexServiceAccountShape.displayLast4(encoded)).isEqualTo("cdef")
    }

    @Test
    fun `API keys, other JSON and non canonical encodings are refused`() {
        assertThat(VertexServiceAccountShape.isValid("AIzaSyFAKEFAKEFAKEFAKE")).isFalse()
        assertThat(VertexServiceAccountShape.isValid(encode(syntheticServiceAccountJson.replace("service_account", "authorized_user")))).isFalse()
        assertThat(VertexServiceAccountShape.isValid(encode(syntheticServiceAccountJson.replace("oauth2.googleapis.com", "evil.example")))).isFalse()
        assertThat(VertexServiceAccountShape.isValid(Base64.getMimeEncoder().encodeToString(syntheticServiceAccountJson.toByteArray()))).isFalse()
        assertThat(VertexServiceAccountShape.isValid(encode(syntheticServiceAccountJson) + "\n")).isFalse()
        val padded = encode(syntheticServiceAccountJson + " ")
        if (padded.endsWith("=")) assertThat(VertexServiceAccountShape.isValid(padded.trimEnd('='))).isFalse()
        assertThat(VertexServiceAccountShape.isValid("")).isFalse()
    }

    @Test
    fun `PEM marker without parseable PKCS8 RSA key is refused`() {
        val malformed =
            syntheticServiceAccountJson.replace(
                validPrivateKey.replace("\n", "\\n"),
                "-----BEGIN PRIVATE KEY-----\\nAAAA\\n-----END PRIVATE KEY-----\\n",
            )
        assertThat(VertexServiceAccountShape.isValid(encode(malformed))).isFalse()
    }

    @Test
    fun `the display tail always fits the stored last4 shape`() {
        val noKeyId = encode(syntheticServiceAccountJson.replace(""""private_key_id":"0123456789abcdef",""", ""))
        assertThat(VertexServiceAccountShape.displayLast4(noKeyId)).matches("^[A-Za-z0-9_-]{4}$")
    }
}
