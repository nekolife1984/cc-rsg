"""M6 acceptance: Kotlin extractor (tree-sitter based, Spring/Ktor/Android-aware).

Tests mirror the Java test pattern but cover Kotlin-specific constructs:
  - data class → schema
  - object → class
  - suspend fun → callable
  - Spring annotations (same @*Mapping as Java)
  - Ktor routing (get/post/put etc.)
"""
from __future__ import annotations

import pytest

from source_map_v2 import extractors
from source_map_v2.model import IdFactory


def _ext(lang, src, path):
    e = extractors.get_extractor(lang)
    return e.extract(path, src, IdFactory()) if e else None


# ---------------------------------------------------------------------------
# Spring Boot Kotlin (same annotations as Java)
# ---------------------------------------------------------------------------
SPRING_KOTLIN = '''\
package com.example

import org.springframework.web.bind.annotation.*
import org.springframework.stereotype.Service
import javax.persistence.Entity

@RestController
@RequestMapping("/api/users")
class UserController {
    @GetMapping("/{id}")
    fun getUser(@PathVariable id: Long): String = "ok"

    @PostMapping
    fun create(): String = "created"
}

@Service
class UserService {
    fun process(): String = "done"
}

@Entity
data class User(
    @Id val id: Long,
    val name: String
)

class PlainClass
'''


@pytest.mark.skipif(extractors.get_extractor("kotlin") is None, reason="no kotlin grammar")
def test_kotlin_spring_and_types():
    units = _ext("kotlin", SPRING_KOTLIN, "src/UserController.kt")
    by = {(u.kind, u.name) for u in units}
    assert ("spring_controller", "UserController") in by
    assert ("spring_service", "UserService") in by
    assert ("jpa_entity", "User") in by
    assert ("kotlin_data_class", "User") in by    # data class → schema
    assert ("kotlin_class", "PlainClass") in by

    eps = [u for u in units if u.kind == "spring_endpoint"]
    methods = {u.endpoint["method"] for u in eps}
    assert {"GET", "POST"} <= methods
    assert any(u.endpoint["path"] == "/{id}" for u in eps)
    assert all(u.role == "endpoint" for u in eps)


# ---------------------------------------------------------------------------
# Kotlin-specific: object, data class, suspend, extension
# ---------------------------------------------------------------------------
KOTLIN_SPECIFIC = '''\
package com.example

data class Person(val name: String, val age: Int)

object AppConfig {
    val version = "1.0"
}

class Calculator {
    suspend fun compute(input: Int): Int = input * 2
}

fun String.isEmail(): Boolean = this.contains("@")

fun topLevel() {
    println("hello")
}
'''


@pytest.mark.skipif(extractors.get_extractor("kotlin") is None, reason="no kotlin grammar")
def test_kotlin_specific_constructs():
    units = _ext("kotlin", KOTLIN_SPECIFIC, "src/example.kt")
    by = {(u.kind, u.name) for u in units}

    assert ("kotlin_data_class", "Person") in by
    assert ("kotlin_data_class", "Person") in by
    assert ("kotlin_object", "AppConfig") in by
    assert ("kotlin_class", "Calculator") in by

    # Functions
    funcs = {(u.kind, u.name) for u in units if u.role == "callable"}
    assert ("kotlin_suspend_function", "compute") in funcs or \
           ("kotlin_function", "compute") in funcs  # suspend vs plain depending on grammar
    assert ("kotlin_function", "topLevel") in funcs


# ---------------------------------------------------------------------------
# Ktor routing
# ---------------------------------------------------------------------------
KTOR = '''\
package com.example

import io.ktor.server.routing.*
import io.ktor.server.response.*
import io.ktor.server.application.*

fun Application.module() {
    routing {
        get("/users") { call.respondText("ok") }
        post("/users") { call.respondText("created") }
        put("/users/{id}") { call.respondText("updated") }
    }
}
'''


@pytest.mark.skipif(extractors.get_extractor("kotlin") is None, reason="no kotlin grammar")
def test_kotlin_ktor_endpoints():
    units = _ext("kotlin", KTOR, "src/KtorModule.kt")
    eps = [u for u in units if u.kind == "ktor_endpoint"]
    methods = {u.endpoint["method"] for u in eps}
    paths = {u.endpoint["path"] for u in eps}

    assert "GET" in methods
    assert "POST" in methods
    assert "/users" in paths
    assert len(eps) >= 2  # at least GET and POST


# ---------------------------------------------------------------------------
# Android-style: just data classes and classes
# ---------------------------------------------------------------------------
ANDROID = '''\
package com.example

@Entity(tableName = "items")
data class Item(
    @PrimaryKey val id: Long,
    val title: String
)

@Dao
interface ItemDao {
    @Query("SELECT * FROM items")
    suspend fun getAll(): List<Item>
}

class ItemRepository(private val dao: ItemDao)
'''


@pytest.mark.skipif(extractors.get_extractor("kotlin") is None, reason="no kotlin grammar")
def test_kotlin_android_style():
    units = _ext("kotlin", ANDROID, "src/Item.kt")
    by = {(u.kind, u.name) for u in units}
    assert ("jpa_entity", "Item") in by or ("kotlin_data_class", "Item") in by
    assert ("kotlin_class", "ItemRepository") in by
