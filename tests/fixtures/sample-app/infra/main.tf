provider "azurerm" {
  features {}
}

resource "azurerm_storage_account" "orders" {
  name = "acmeorders"
}

module "network" {
  source = "./modules/network"
}
